function cfg = project_config()
%PROJECT_CONFIG Central path configuration for the migrated 4-story project.

codeDir = fileparts(mfilename('fullpath'));
cfg.root = fileparts(fileparts(codeDir));

cfg.raw_data_dir = fullfile(cfg.root, 'data', 'raw');
cfg.processed_text_dir = fullfile(cfg.root, 'data', 'processed', 'text');
cfg.spreadsheets_dir = fullfile(cfg.root, 'results', 'spreadsheets');
cfg.figures_dir = fullfile(cfg.root, 'results', 'figures');
cfg.runtime_data_loop_dir = fullfile( ...
    cfg.root, 'results', 'runtime', 'data_loop');
cfg.metadata_dir = fullfile(cfg.root, 'metadata');
cfg.folder_list_file = fullfile(cfg.metadata_dir, 'folder_list.xlsx');
cfg.sensor_list_file = fullfile(cfg.metadata_dir, 'sensor_list.xlsx');
cfg.documents_dir = fullfile(cfg.root, 'documents');
end
