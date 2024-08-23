import logging
import gradio as gr
import yaml
import subprocess
import sys
import os
from gradio_log import Log
import chardet

logging.basicConfig(level=logging.DEBUG)


def read_yaml_file(file_path):
    try:
        # Detect the file encoding
        with open(file_path, 'rb') as raw_file:
            raw_data = raw_file.read()
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

        # Read the file with the detected encoding
        with open(file_path, "r", encoding=file_encoding) as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}
      
config = {}
config_file_path = 'config.yaml'
config = read_yaml_file(config_file_path)
components = [] # so we create a list of components



for key1 in config: # for each key in the config
    group = [] # make a group?
    for key2 in config[key1]: # for each subkey/actual value
        group.append({'path': [key1, key2], 'label':key2, 'value':config[key1][key2]}) # make a path through the config, label, and give    it the value 
    components.append(group) # append this stuff to components. Does gradio seriously take a list of dicts?

def changed(text, keys): # updates the global config dictionary when a textbox is changed. It also provides the path to the thing to change in the config, that's what we change.
    print("\nDEBUG")
    print(keys)
    global config
    _config = config
    for key in keys[:-1]:
        _config = _config.setdefault(key, {}) # create nested dicts if they don't exist for all keys except the final level of the nested structure
    _config[keys[-1]] = text # update the VALUE at the final level of the nested structure with the new text
    return keys

def run(file): # dumps the current config to the config file, then runs the processing script. I think we can repurpose much of this for the new thing.
    global config
    try:
        with open(config_file_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, allow_unicode=True)
    except Exception as e:
        print(f"Error writing config file: {e}")
        return  
    try:
        env = os.environ.copy()
        with open("log.txt", "w", encoding='utf-8') as log_file:
            subprocess.run([sys.executable, "processing.py"], stdout=log_file, stderr=log_file, text=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def scan_for_valid_scripts():
    valid_scripts = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(current_dir):
        if os.path.isdir(item) and os.path.exists(os.path.join(item, "processing.py")):
            valid_scripts.append(item)
    return valid_scripts


def create_config_components(config):
    components = []
    for key1 in config:
        group = []
        for key2 in config[key1]:
            group.append({'path': [key1, key2], 'label': key2, 'value': config[key1][key2]})
        components.append(group)
    logging.debug(f"Created components: {components}")
    return components

# def update_config_display(folder, path):
#     logging.debug(f"Updating config display for {folder} with path {path}")
#     if os.path.exists(path):
#         # config = read_yaml_file(path)
#         with open(path, 'r') as f:
#             config = yaml.safe_load(f)
#         logging.debug(f"Config contents: {config}")
#         components = create_config_components(config)
#         logging.debug(f"Created components: {components}")
#         return gr.update(visible=True), gr.update(visible=False), components
#     else:
#         logging.warning(f"Config file not found: {path}")
#         return gr.update(visible=False), gr.update(visible=True, value=f"Warning: Config file not found for {folder}"), []

# Once I put out the competition, it'll be $1000 to the best pipeline, and a $200 bounty to the person who can make the gradio nice and nested etc.

with gr.Blocks(css="#log { padding:0; height: 0; overflow: hidden; } #log.display { padding: 10px 12px; height: auto; overflow: auto; } .gradio-container { max-width: none !important; }") as demo:
    with gr.Row():
      log_file = os.path.abspath("log.txt")
      if not os.path.isfile(log_file):
          open(log_file, 'w').close()
      with open(log_file, "w", encoding='utf-8') as file:
          file.truncate(0)
      log_view = Log(log_file, xterm_font_size=12, dark=True, elem_id='log')
    with gr.Row():
      file = gr.File()
      btn = gr.Button("Start", elem_id="start")
      btn.click(
          fn=run,
          inputs=[file],
          outputs=[],
          js='(e) => { document.querySelector("#log").classList.add("display") }'
      )
    valid_scripts = scan_for_valid_scripts()
    
    for script in valid_scripts:
        with gr.Column():
            visible = gr.State(False)
            with gr.Row():
                script_textbox = gr.Textbox(label=f"{script} Config Path", value=f"config.yaml", interactive=True)
                script_enable = gr.Checkbox(label="Use Pipeline (enable to see settings)")
            with gr.Row(visible=False) as specific_config_settings:
                # TODO code in here to dynamically create settings based on config contents. And yes it has to be dynamic different pipelines have different settings.
                gr.Textbox(label="I AM A PLACEHOLDER")
        
            def flip_config_visibility(visible_state):
                return gr.Row(visible=(not visible_state)), gr.State(not visible_state)
            script_enable.change(
                flip_config_visibility,
                inputs=[visible],
                outputs=[specific_config_settings, visible]
            )
            
                
        # We then need to create components, FOR EACH CONFIG, IFF the checkbox is enabled and the path matches.
    
        with gr.Row():
            for component in components:
                with gr.Column():
                    for item in component:
                        t = gr.Textbox(label=item['label'], value=item['value'], interactive=True)
                        t.change(changed, [t, gr.State(value=item['path'])], [gr.State()])
   
demo.launch()