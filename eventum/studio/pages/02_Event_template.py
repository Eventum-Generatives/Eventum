import streamlit as st

from eventum.studio.components.component import persist_state
from eventum.studio.components.template_configuration_editor import \
    TemplateConfigurationEditor
from eventum.studio.components.template_editor import TemplateEditor
from eventum.studio.components.template_manager import TemplateManager
from eventum.studio.components.template_renderer import TemplateRenderer
from eventum.studio.components.template_state_viewer import TemplateStateViewer
from eventum.studio.theme import apply_theme

persist_state()
st.set_page_config(
    page_title='Eventum Studio',
    layout='wide',
    initial_sidebar_state='expanded'
)
apply_theme()

for key in ['template_content', 'config_content']:
    if key not in st.session_state:
        st.session_state[key] = ''

manager = TemplateManager(
    props={
        'get_content_callback': lambda: st.session_state['template_content'],
        'set_content_callback': (
            lambda content:
            st.session_state.__setitem__('template_content', content)
        )
    }
)
editor = TemplateEditor(
    props={
        'content': st.session_state['template_content'],
        'read_only': manager.is_empty,
        'on_change': (
            lambda value:
            st.session_state.__setitem__('template_content', value)
        )
    }
)
config_editor = TemplateConfigurationEditor(
    props={
        'on_change': (
            lambda value:
            st.session_state.__setitem__('config_content', value)
        )
    }
)
renderer = TemplateRenderer(
    props={
        'template_content': st.session_state['template_content'],
        'configuration_content': config_editor.content
    }
)
state_viewer = TemplateStateViewer()

with st.sidebar:
    manager.show()

editor_tab, configuration_tab, rendering_tab, state_tab = st.tabs(
    ['Template', 'Configuration', 'Rendering', 'State']
)

with editor_tab:
    editor.show()

with configuration_tab:
    config_editor.show()

with rendering_tab:
    renderer.show()

with state_tab:
    state_viewer.show()
