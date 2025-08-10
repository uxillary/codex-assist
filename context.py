class AppContext:
    """Holds shared application state."""
    def __init__(self):
        self.settings = {
            'use_project_context': True,
            'show_prompt_cost': True,
            'auto_load_last_project': True,
            'include_history': False,
            'theme': 'darkly',
            'last_project': '',
        }
        self.model = 'gpt-3.5-turbo'
        self.total_tokens = 0
        self.active_project = ''
        self.context_summary = {}
        self.generated_files = []
        self.history_path = 'data/history.json'
        self.settings_path = 'data/settings.json'
        self.summaries_path = 'data/summaries.json'
        self.project_file = 'data/active_project.codexproj'


__all__ = ['AppContext']
