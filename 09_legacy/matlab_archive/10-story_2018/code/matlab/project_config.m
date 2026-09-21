function cfg = project_config()
%PROJECT_CONFIG Return canonical paths for the 2018 10-story project.

code_dir = fileparts(mfilename('fullpath'));
cfg.root = fileparts(fileparts(code_dir));
cfg.raw_data_dir = fullfile(cfg.root, 'data', 'raw');
cfg.processed_text_dir = fullfile(cfg.root, 'data', 'processed', 'text');
cfg.matlab_spreadsheets_dir = fullfile(cfg.root, 'results', 'matlab', 'spreadsheets');
cfg.matlab_runtime_dir = fullfile(cfg.root, 'results', 'runtime', 'matlab', 'data_loop');
cfg.metadata_dir = fullfile(cfg.root, 'metadata');
cfg.folder_list_file = fullfile(cfg.metadata_dir, 'folder_list.xlsx');
cfg.documents_dir = fullfile(cfg.root, 'documents');
end
