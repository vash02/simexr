import os
import streamlit.components.v1 as components

_RELEASE = True if os.environ.get('PKG_DEVELOPMENT') is None else False
if not _RELEASE:
    _component_func = components.declare_component(
        "gradio_streamlit",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component("gradio_streamlit", path=build_dir)

def gradio_streamlit_input(config):
    config['componentType'] = 'input'
    component_value = _component_func(config=config)
    return component_value
  
def gradio_streamlit_output(config, output=None):
    config['componentType'] = 'output'
    _component_func(config=config, output=output)