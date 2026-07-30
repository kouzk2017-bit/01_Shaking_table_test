%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       
dt = 1/1000;          
k = 20;               
cutLHz = 0.05;        
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

%% 数据读取 (JB11：1-10通道为1，2，3，4，6层节点位移)
fprintf('>> 正在处理案例: %s (提取位移数据)\n', directory);
jb_list = [11]; 
CH_counts = {1:12}; 

Disp_Raw = [];
for j = 1:length(jb_list)
    jb_now = jb_list(j);
    csv_file = fullfile(cfg.raw_data_dir, test_date, test_folder, sprintf('%s%d.csv', csv_prefix, jb_now));
    
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
disp_filtered = Fn_filtering(Disp_Raw, 1/dt, [cutLHz cutHHz], 'fft_BPF');
Disp = Fn_Resampling(disp_filtered, dt, new_dt);

%% 计算节点转角 (Gamma)
% 梁高W，柱宽H
W_array = [550, 500, 500, 500, 500, 500]; 
H = 500;

% 从图片表格提取尺寸 (每一行对应 D1-D10)
% A1, A2 对应水平偏移；B1, B2 对应垂直偏移
A1 = [100 100 100 100 100 100 53 50 100 100 60 60 55 60 100 100 100 100 78 78];
A2 = [100 100 100 100 100 100 60 60 100 100 55 55 60 60 100 100 100 100 78 78];
B1 = [60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60];
B2 = [60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60 60];

% 通道映射：[对角线1, 对角线2] -> 每组两个通道，计算 (delta2 - delta1)
% 对应 1F: [1,2], 2F: [3,4], 3F: [5,6], 4F: [7,8], 5F: [9,10], 6F: [11,12]
mapping = [1, 2; 3, 4; 5, 6; 7, 8; 9, 10; 11, 12];
num_nodes = size(mapping, 1);

Gamma_Matrix = zeros(size(Disp, 1), num_nodes);

for i = 1:num_nodes
    idx_low  = mapping(i, 1); % 对角线1 通道索引
    idx_high = mapping(i, 2); % 对角线2 通道索引
    
    % --- 几何参数计算 ---
    % 获取当前楼层对应的梁高
    cur_W = W_array(i);
    
    % 计算当前节点两个测点的有效跨度 a (垂直) 和 b (水平)
    % a = H - B1 - B2
    a_low  = H - B1(idx_low) - B2(idx_low);
    a_high = H - B1(idx_high) - B2(idx_high);
    
    % b = W - A1 - A2
    b_low  = cur_W - A1(idx_low) - A2(idx_low);
    b_high = cur_W - A1(idx_high) - A2(idx_high);
    
    % 取两个位移计对应跨度的平均值
    cur_a = (a_low + a_high) / 2;
    cur_b = (b_low + b_high) / 2;
    
    % --- 核心公式计算 ---
    % 计算公式系数: $coeff = \frac{\sqrt{a^2 + b^2}}{2ab}$
    coeff = sqrt(cur_a^2 + cur_b^2) / (2 * cur_a * cur_b);
    
    % 计算节点转角 Gamma
    Gamma_Matrix(:, i) = coeff * (Disp(:, idx_low) - Disp(:, idx_high));
end

%% Excel 导出
excelDir = cfg.matlab_spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Joint_' directory '.xlsx']);

t = (0:new_dt:new_dt*(size(Gamma_Matrix,1)-1))';
floor_labels = {'1F', '2F', '3F', '4F', '5F', '6F'};

header_gamma = [{'Time_s'}, cellfun(@(s) [s, '_rad'], floor_labels, 'UniformOutput', false)];
T_gamma = cell2table([num2cell(t), num2cell(Gamma_Matrix)], 'VariableNames', header_gamma);
writetable(T_gamma, MasterFileName, 'Sheet', 'NodeRotation');
