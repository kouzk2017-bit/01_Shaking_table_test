%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       
dt = 1/1000;          
k = 22;               
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
jb_list = [11]; 
CH_counts = {1:38}; 

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
% 根据图示公式：gamma = (sqrt(a^2 + b^2) / 2ab) * (delta1 - delta2)
% 参数定义 (单位: mm)
% a = 550 - (50 + 80);
% b = 500 - (107 + 107);
a = 270;
b = 270;

% 计算公式系数
coeff = sqrt(a^2 + b^2) / (2 * a * b);

% 通道映射：JB11的前10个通道对应 1F, 2F, 3F, 4F, 6F 的 delta1 和 delta2
% 1F:CH1,2 | 2F:CH3,4 | 3F:CH5,6 | 4F:CH7,8 | 6F:CH9,10
floor_indices = [1, 2; 3, 4; 5, 6; 7, 8; 9, 10];
floor_labels = {'1F', '2F', '3F', '4F', '6F'};

Gamma_Matrix = zeros(size(Disp, 1), 5); % 初始化结果矩阵

for i = 1:5
    idx1 = floor_indices(i, 1);
    idx2 = floor_indices(i, 2);
    % delta1 和 delta2 为 mm，计算结果 gamma 为 rad
    Gamma_Matrix(:, i) = coeff * (Disp(:, idx1) - Disp(:, idx2));
end

%% Excel 导出
excelDir = cfg.spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Joint_' directory '.xlsx']);
t = (0:new_dt:new_dt*(size(Gamma_Matrix,1)-1))';

header_gamma = [{'Time_s'}, cellfun(@(s) [s, '_rad'], floor_labels, 'UniformOutput', false)];
T_gamma = cell2table([num2cell(t), num2cell(Gamma_Matrix)], 'VariableNames', header_gamma);
writetable(T_gamma, MasterFileName, 'Sheet', 'NodeRotation');
