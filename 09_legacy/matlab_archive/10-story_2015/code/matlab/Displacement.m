%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       
dt = 1/1000;          
k = 22;
cutLHz = 0.02;        
cutHHz = 100;          

%% 获取路径与元数据
cfg = project_config();

[~, folder_list] = xlsread(cfg.folder_list_file);
directory      = cell2mat(folder_list(k,1));
test_date      = cell2mat(folder_list(k,2));
test_folder    = cell2mat(folder_list(k,3));
csv_prefix     = cell2mat(folder_list(k,4));

txtdir = fullfile(cfg.processed_text_dir, test_date, test_folder);
if ~exist(txtdir, 'dir'), mkdir(txtdir); end
imagedir = fullfile(cfg.figures_dir, test_date, test_folder);
if ~exist(imagedir, 'dir'), mkdir(imagedir); end

%% 数据读取 (JB7的56个通道和JB10的1-24通道是层间位移)
fprintf('>> 正在处理案例: %s\n', directory);
jb_list = [7 10];
CH_counts = {1:56, 1:60}; 

Disp_Raw = [];
for j = 1:length(jb_list)
    jb_now = jb_list(j);
    csv_file = fullfile(cfg.raw_data_dir, test_date, test_folder, sprintf('%s%02d.csv', csv_prefix, jb_now));
    
    if isfile(csv_file)
        opts = detectImportOptions(csv_file);
        opts.DataLines = [4 Inf]; 
        Tcsv = readtable(csv_file, opts);
        
        current_CHs = CH_counts{j};
        for ch = current_CHs
            ch_data = Tcsv{:, ch + 1};
            Disp_Raw(:, end+1) = ch_data; 
            % 自动备份 TXT
            try writematrix(ch_data, fullfile(txtdir, sprintf('JB%d_CH%d.txt', jb_now, ch)), 'Delimiter', 'tab'); catch; end
        end
    end
end

%% 信号处理
% disp_filtered = Fn_filtering(Disp_Raw, 1/dt, [cutLHz cutHHz], 'fft_BPF');
% Disp = Fn_Resampling(disp_filtered, dt, new_dt);
Disp = Fn_Resampling(Disp_Raw, dt, new_dt);

%% 基本参数与层高设置
H = [2800 2600 2600 2600 2550 2550 2550 2500 2500 2500]; % 楼层高(mm)

%% 提取并计算位移
% 提取 X/Y 方向位移计 (每8个通道一个循环)
dispx_NWT = Disp(:,1:8:73);
dispx_NWB = Disp(:,2:8:74);
dispy_NWT = Disp(:,3:8:75);
dispy_NWB = Disp(:,4:8:76);

dispx_SET = Disp(:,5:8:77);
dispx_SEB = Disp(:,6:8:78);
dispy_SET = Disp(:,7:8:79);
dispy_SEB = Disp(:,8:8:80);

% 特殊情况修正（实验人员提供）
if k==10
    dispx_SET(:,6) = dispx_NWT(:,6);
end

% 计算当前工况测得的位移 (平均值)（TOP+BOTTOM 或 NWT+SET）
Dispx_raw = (dispx_NWT + dispx_SET)/2;
Dispy_raw = (dispy_NWT + dispy_SET)/2;

% 层间位移（相对于各层地面的位移）
RelDispx = Dispx_raw; 
RelDispy = Dispy_raw;

% 计算转角 (依然使用各层自身的净位移 dUx / dUy 除以对应层高)
Radx = RelDispx ./ H;
Rady = RelDispy ./ H;

% 绝对位移：叠加计算（相对于地面的总位移)
AbsDispx = cumsum(RelDispx, 2); 
AbsDispy = cumsum(RelDispy, 2); 

%% 累积损伤位移计算 （在上一步的前提下加入参与位移从而计算累积位移)
% 定义 knum 用于残余位移追踪
knum_map = [2,4,7,10,13,15,17,20,22];
[~, knum] = ismember(k, knum_map);

% 实验类型与编号逻辑
if ismember(k, knum_map)
    kname = 1; % 主震试验
else
    kname = 0; % White Noise
end

TotalRelDispx = RelDispx;
TotalRelDispy = RelDispy;

if kname == 1
    res_dir = cfg.runtime_data_loop_dir;
    if ~exist(res_dir, 'dir'), mkdir(res_dir); end
    res_path = fullfile(res_dir, sprintf('residual_disp_%d.mat', knum-1));
    
    if exist(res_path, 'file')
        load(res_path); % 加载上一工况遗留的变量 res_dispx, res_dispy
        
        % 计算累积位移 (当前位移 + 上一工况终点的残余位移)
        TotalRelDispx = RelDispx + res_dispx;
        TotalRelDispy = RelDispy + res_dispy;
    end
    
    % 【关键】保存当前累积序列的最后一行，作为下一个工况的起始残余点
    res_dispx = TotalRelDispx(end,:); 
    res_dispy = TotalRelDispy(end,:);
    save(fullfile(res_dir, sprintf('residual_disp_%d.mat', knum)), 'res_dispx', 'res_dispy');
end

% 基于累积位移重新计算累积转角
TotalRadx = TotalRelDispx ./ H;
TotalRady = TotalRelDispy ./ H;

% 绝对位移也建议基于累积位移计算
TotalAbsDispx = cumsum(TotalRelDispx, 2); 
TotalAbsDispy = cumsum(TotalRelDispy, 2);

%% Excel 导出 (包含当前工况与累积损伤数据)
excelDir = cfg.spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Drift_Results_' regexprep(directory, '[^\w]', '_') '.xlsx']);
t = (0:size(AbsDispx,1)-1)' * new_dt;

% --- 表头定义 ---
floor_names = [arrayfun(@(i) sprintf('%dF_mm', i), 2:10, 'UniformOutput', false), {'RF_mm'}];
header_dis = [{'Time_s'}, floor_names];
header_rad = [{'Time_s'}, arrayfun(@(i) sprintf('%dF_rad', i), 1:10, 'UniformOutput', false)];

% --- 1. 写入当前工况数据 (Current Run) ---
% 导出相对位移 (当前)
writetable(array2table([t, RelDispx], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'RelDispX');
writetable(array2table([t, RelDispy], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'RelDispY');
% 导出绝对位移 (当前)
writetable(array2table([t, AbsDispx], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'AbsDispX');
writetable(array2table([t, AbsDispy], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'AbsDispY');
% 导出转角 (当前)
writetable(array2table([t, Radx], 'VariableNames', header_rad), MasterFileName, 'Sheet', 'RadX');
writetable(array2table([t, Rady], 'VariableNames', header_rad), MasterFileName, 'Sheet', 'RadY');

% --- 2. 写入累积损伤数据 (Accumulated Total) ---
% 如果 kname == 1 (主震工况)，导出叠加了残余位移后的数据
if kname == 1
    % 导出累积相对位移
    writetable(array2table([t, TotalRelDispx], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'TotalRelDispX');
    writetable(array2table([t, TotalRelDispy], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'TotalRelDispY');
    % 导出累积绝对位移
    writetable(array2table([t, TotalAbsDispx], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'TotalAbsDispX');
    writetable(array2table([t, TotalAbsDispy], 'VariableNames', header_dis), MasterFileName, 'Sheet', 'TotalAbsDispY');
    % 导出累积转角
    writetable(array2table([t, TotalRadx], 'VariableNames', header_rad), MasterFileName, 'Sheet', 'TotalRadX');
    writetable(array2table([t, TotalRady], 'VariableNames', header_rad), MasterFileName, 'Sheet', 'TotalRadY');
    
    fprintf('>>> 已添加累积损伤数据至 Excel。\n');
else
    fprintf('>>> 当前为 White Noise 工况，未输出累积损伤数据。\n');
end

fprintf('>>> 全部数据已保存至: %s\n', MasterFileName);
