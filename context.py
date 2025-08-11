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
            'verbose': True,
            'activity_console_visible': True,
            'activity_log_file': None,
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

        self._load_settings()
        try:
            from logging_bus import set_verbose, set_file_logger
            set_verbose(self.settings.get('verbose', True))
            set_file_logger(self.settings.get('activity_log_file'))
        except Exception:
            pass

    def _load_settings(self) -> None:
        import json
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.settings.update(data)
        except Exception:
            pass

    def save_settings(self) -> None:
        import json, os
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass


__all__ = ['AppContext']
