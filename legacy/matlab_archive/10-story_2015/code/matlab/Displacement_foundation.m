%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       % 重采样后时间间隔，100 Hz
dt = 1/1000;          % 原始采样时间间隔，1000 Hz

k = 4;

cutLHz = 0.02;        % 滤波下限
cutHHz = 100;         % 滤波上限，保持你原来的设置

use_filter = true;    % 是否滤波
use_resample = true;  % 是否重采样

%% 获取路径与元数据
cfg = project_config();

[~, folder_list] = xlsread(cfg.folder_list_file);

directory   = cell2mat(folder_list(k,1));
test_date   = cell2mat(folder_list(k,2));
test_folder = cell2mat(folder_list(k,3));
csv_prefix  = cell2mat(folder_list(k,4));

fprintf('>> 正在处理案例: %s\n', directory);

%% 输出文件夹
excelDir = cfg.spreadsheets_dir;
if ~exist(excelDir, 'dir')
    mkdir(excelDir);
end

MasterFileName = fullfile(excelDir, ...
    ['SLP_Displacement_' regexprep(directory, '[^\w]', '_') '.xlsx']);

% 如果已有同名 Excel，先删除，避免残留旧工作表
if exist(MasterFileName, 'file')
    delete(MasterFileName);
end

%% 指定 JB、通道和位移计名称

% JB10：25-32通道
JB10_channels = 25:32;
JB10_names = { ...
    'SLP-DX-SSW', ...
    'SLP-DY-WSW', ...
    'SLP-DY-WNW', ...
    'SLP-DX-NNW', ...
    'SLP-DX-NNE', ...
    'SLP-DY-ENE', ...
    'SLP-DY-ESE', ...
    'SLP-DX-SSE'};

% JB11：51-54通道
JB11_channels = 51:54;
JB11_names = { ...
    'SLP-DX-SSW-W', ...
    'SLP-DX-NNW-W', ...
    'SLP-DX-NNE-W', ...
    'SLP-DX-SSE-W'};

%% 读取全部指定通道

All_Raw = [];
All_names = {};
All_dir = {};

%% ========== 读取 JB10 ==========
jb_now = 10;
csv_file = fullfile(cfg.raw_data_dir, test_date, test_folder, ...
    sprintf('%s%02d.csv', csv_prefix, jb_now));

if isfile(csv_file)

    opts = detectImportOptions(csv_file);
    opts.DataLines = [4 Inf];
    Tcsv = readtable(csv_file, opts);

    for i = 1:length(JB10_channels)

        ch = JB10_channels(i);
        sensor_name = JB10_names{i};

        % 保持你原来的读取逻辑：CH25 对应表格第 26 列
        ch_data = Tcsv{:, ch + 1};

        All_Raw(:, end+1) = ch_data;
        All_names{end+1} = sensor_name;

        if contains(sensor_name, '-DX-')
            All_dir{end+1} = 'X';
        elseif contains(sensor_name, '-DY-')
            All_dir{end+1} = 'Y';
        else
            All_dir{end+1} = 'Unknown';
        end
    end

else
    warning('未找到文件: %s', csv_file);
end

%% ========== 读取 JB11 ==========
jb_now = 11;
csv_file = fullfile(cfg.raw_data_dir, test_date, test_folder, ...
    sprintf('%s%02d.csv', csv_prefix, jb_now));

if isfile(csv_file)

    opts = detectImportOptions(csv_file);
    opts.DataLines = [4 Inf];
    Tcsv = readtable(csv_file, opts);

    for i = 1:length(JB11_channels)

        ch = JB11_channels(i);
        sensor_name = JB11_names{i};

        % 保持你原来的读取逻辑
        ch_data = Tcsv{:, ch + 1};

        All_Raw(:, end+1) = ch_data;
        All_names{end+1} = sensor_name;

        if contains(sensor_name, '-DX-')
            All_dir{end+1} = 'X';
        elseif contains(sensor_name, '-DY-')
            All_dir{end+1} = 'Y';
        else
            All_dir{end+1} = 'Unknown';
        end
    end

else
    warning('未找到文件: %s', csv_file);
end

%% 检查是否读取到数据
if isempty(All_Raw)
    error('没有读取到任何位移数据，请检查 CSV 路径、JB编号和通道号。');
end

fprintf('>>> 已读取 %d 个位移通道。\n', size(All_Raw, 2));

%% 滤波与重采样

Disp_process = All_Raw;

% 1. 滤波
if use_filter
    fprintf('>>> 正在滤波: %.3f Hz - %.3f Hz\n', cutLHz, cutHHz);
    Disp_process = Fn_filtering(Disp_process, 1/dt, [cutLHz cutHHz], 'fft_BPF');
end

% 2. 重采样
if use_resample
    fprintf('>>> 正在重采样: %.0f Hz -> %.0f Hz\n', 1/dt, 1/new_dt);
    Disp_process = Fn_Resampling(Disp_process, dt, new_dt);
    export_dt = new_dt;
else
    export_dt = dt;
end

%% 按 X / Y 方向分组

isX = strcmp(All_dir, 'X');
isY = strcmp(All_dir, 'Y');

Disp_X = Disp_process(:, isX);
Disp_Y = Disp_process(:, isY);

X_names = All_names(isX);
Y_names = All_names(isY);

t = (0:size(Disp_process, 1)-1)' * export_dt;

%% 导出 X 方向位移时程

if ~isempty(Disp_X)

    header_X = [{'Time_s'}, X_names];

    writecell(header_X, MasterFileName, 'Sheet', 'Disp_X', 'Range', 'A1');
    writematrix([t, Disp_X], MasterFileName, 'Sheet', 'Disp_X', 'Range', 'A2');

    fprintf('>>> X方向位移时程已导出，共 %d 个通道。\n', size(Disp_X, 2));

else
    warning('没有读取到 X 方向位移数据。');
end

%% 导出 Y 方向位移时程

if ~isempty(Disp_Y)

    header_Y = [{'Time_s'}, Y_names];

    writecell(header_Y, MasterFileName, 'Sheet', 'Disp_Y', 'Range', 'A1');
    writematrix([t, Disp_Y], MasterFileName, 'Sheet', 'Disp_Y', 'Range', 'A2');

    fprintf('>>> Y方向位移时程已导出，共 %d 个通道。\n', size(Disp_Y, 2));

else
    warning('没有读取到 Y 方向位移数据。');
end

fprintf('>>> 全部位移时程数据已保存至: %s\n', MasterFileName);
