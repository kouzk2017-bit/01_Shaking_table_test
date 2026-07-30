%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       
dt = 1/1000;          
k = 14;               
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
imagedir = fullfile(cfg.figures_dir, test_date, test_folder);
if ~exist(imagedir, 'dir'), mkdir(imagedir); end

%% 数据读取 (JB11：1-10通道为1，2，3，4，6层节点位移)
fprintf('>> 正在处理案例: %s (提取位移数据)\n', directory);
jb_list = [4]; 
CH_counts = {1:60}; 

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

%% 计算节点转角 (Gamma)
% 梁高W，柱宽H
W = 500; 
H = 600;

% 从图片表格提取尺寸 (每一行对应 D1-D10)
% A1, A2 对应水平偏移；B1, B2 对应垂直偏移
A1 = [82, 85, 85, 85, 89, 90, 85, 85, 90, 100];
A2 = [85, 83, 94, 84, 95, 91, 86, 80, 84, 92];
B1 = [52, 48, 56, 55, 55, 48, 50, 52, 55, 50];
B2 = [88, 90, 75, 84, 68, 80, 74, 70, 70, 76];

% 计算测点间的有效跨度 a 和 b
a = H - B1 - B2; 
b = W - A1 - A2;

% 通道映射：[对角线2, 对角线1] -> 对应 [减数, 被减数] 实现 (delta2 - delta1)
% 1F:[52-51], 2F:[54-53], 3F_Mid:[56-55], 3F_NE:[58-57], 4F:[60-59]
mapping = [51, 52; 53, 54; 55, 56; 57, 58; 59, 60];
floor_labels = {'1F', '2F', '3F_EastMid', '3F_NE', '4F'};
num_nodes = size(mapping, 1);

Gamma_Matrix = zeros(size(Disp, 1), num_nodes);

for i = 1:num_nodes
    idx_low  = mapping(i, 1); % 例如 51
    idx_high = mapping(i, 2); % 例如 52
    
    % 获取对应的几何参数索引 (51-60 对应 1-10)
    k1 = idx_low - 50;
    k2 = idx_high - 50;
    
    % 取两个位移计对应 a 和 b 的平均值
    cur_a = (a(k1) + a(k2)) / 2;
    cur_b = (b(k1) + b(k2)) / 2;
    
    % 计算公式系数: sqrt(a^2 + b^2) / (2 * a * b)
    % 这是导致数量级差异的关键，分母 2ab 非常大
    coeff = sqrt(cur_a^2 + cur_b^2) / (2 * cur_a * cur_b);

    % 按照您的要求：52列减51列 (delta2 - delta1)
    % 如果位移计受压为负，则此差值代表了剪切变形的差量
    Gamma_Matrix(:, i) = coeff * (Disp(:, idx_high) - Disp(:, idx_low));
end

%% Excel 导出
excelDir = cfg.spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Joint_' directory '.xlsx']);

t = (0:new_dt:new_dt*(size(Gamma_Matrix,1)-1))';
% 修正 cellfun 报错：直接使用定义好的 floor_labels
header_gamma = [{'Time_s'}, cellfun(@(s) [s, '_rad'], floor_labels, 'UniformOutput', false)];

T_gamma = cell2table([num2cell(t), num2cell(Gamma_Matrix)], 'VariableNames', header_gamma);
writetable(T_gamma, MasterFileName, 'Sheet', 'NodeRotation');
