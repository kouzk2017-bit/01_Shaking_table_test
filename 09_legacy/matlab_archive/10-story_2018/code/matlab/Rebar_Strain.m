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
fprintf('>> 正在处理案例: %s (提取钢筋应变数据)\n', directory);
jb_list = [4 5 6]; 
CH_counts = {1:64; 1:64; 1:64}; 

Rebar_Strain_Raw = [];
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
            Rebar_Strain_Raw(:, end+1) = ch_data; 
            % 自动备份 TXT
            try writematrix(ch_data, fullfile(txtdir, sprintf('JB%d_CH%d.txt', jb_now, ch)), 'Delimiter', 'tab'); catch; end
        end
    end
end

%% 信号处理
strain_filtered = Fn_filtering(Rebar_Strain_Raw, 1/dt, [cutLHz cutHHz], 'fft_BPF');
Strain_Resampled = Fn_Resampling(strain_filtered, dt, new_dt);

%% 仅提取与计算目标核心数据

% 4F 2A 位置 下部柱 (8-17列处理)
Col_4F_L = [ ...
    Strain_Resampled(:, 8), ... % 右下角纵筋
    Strain_Resampled(:, 10), ... % 右上角纵筋
    Strain_Resampled(:, 13), ... % 左下角纵筋
    Strain_Resampled(:, 15), ... % 左上角纵筋
    Strain_Resampled(:, 16), ... % 箍筋(上下)
    Strain_Resampled(:, 17)  ... % 箍筋(左右)
];

% 4F 2A 位置 上部柱 (18-27列处理)
Col_4F_U = [ ...
    Strain_Resampled(:, 18), ... % 右下角纵筋
    Strain_Resampled(:, 20), ... % 右上角纵筋
    Strain_Resampled(:, 23), ... % 左下角纵筋
    Strain_Resampled(:, 25), ... % 左上角纵筋
    Strain_Resampled(:, 26), ... % 箍筋(上下)
    Strain_Resampled(:, 27)  ... % 箍筋(左右)
];

% 4F 2A 位置 左侧梁 (33-37列处理)
Beam_4F_L = [ ...
    Strain_Resampled(:, 33), ... % 左上角纵筋
    Strain_Resampled(:, 36), ... % 左下角纵筋
    Strain_Resampled(:, 37)  ... % 箍筋
];

% 4F 2A 位置 右侧梁 (38-42列处理)
Beam_4F_R = [ ...
    Strain_Resampled(:, 38), ... % 左上角纵筋
    Strain_Resampled(:, 41), ... % 左下角纵筋
    Strain_Resampled(:, 42)  ... % 箍筋
];

% 3F 2A 位置 上部柱 (82-91列处理)
Col_3F_U = [ ...
    Strain_Resampled(:, 82), ... % 右下角纵筋
    Strain_Resampled(:, 84), ... % 右上角纵筋
    Strain_Resampled(:, 87), ... % 左下角纵筋
    Strain_Resampled(:, 89), ... % 左上角纵筋
    Strain_Resampled(:, 90), ... % 箍筋(上下)
    Strain_Resampled(:, 91)  ... % 箍筋(左右)
];

% 5F 2A 位置 下部柱 (142-151列处理)
Col_5F_L = [ ...
    Strain_Resampled(:, 142), ... % 右下角纵筋
    Strain_Resampled(:, 144), ... % 右上角纵筋
    Strain_Resampled(:, 147), ... % 左下角纵筋
    Strain_Resampled(:, 149), ... % 左上角纵筋
    Strain_Resampled(:, 150), ... % 箍筋(上下)
    Strain_Resampled(:, 151)  ... % 箍筋(左右)
];

% 5F 2A 位置 上部柱 (152-161列处理)
Col_5F_U = [ ...
    Strain_Resampled(:, 152), ... % 右下角纵筋
    Strain_Resampled(:, 154), ... % 右上角纵筋
    Strain_Resampled(:, 157), ... % 左下角纵筋
    Strain_Resampled(:, 159), ... % 左上角纵筋
    Strain_Resampled(:, 160), ... % 箍筋(上下)
    Strain_Resampled(:, 161)  ... % 箍筋(左右)
];

% 5F 2A 位置 左侧梁 (162-166列处理)
Beam_5F_L = [ ...
    Strain_Resampled(:, 162), ... % 左上角纵筋
    Strain_Resampled(:, 165), ... % 左下角纵筋
    Strain_Resampled(:, 166)  ... % 箍筋
];

% 5F 2A 位置 右侧梁 (167-171列处理)
Beam_5F_R = [ ...
    Strain_Resampled(:, 167), ... % 左上角纵筋
    Strain_Resampled(:, 170), ... % 左下角纵筋
    Strain_Resampled(:, 171)  ... % 箍筋
];

% 6F 2A 位置 左侧梁 (172-176列处理)
Beam_6F_L = [ ...
    Strain_Resampled(:, 172), ... % 左上角纵筋
    Strain_Resampled(:, 175), ... % 左下角纵筋
    Strain_Resampled(:, 176)  ... % 箍筋
];

% 6F 2A 位置 右侧梁 (177-181列处理)
Beam_6F_R = [ ...
    Strain_Resampled(:, 177), ... % 左上角纵筋
    Strain_Resampled(:, 180), ... % 左下角纵筋
    Strain_Resampled(:, 181)  ... % 箍筋
];

% 6F 2A 位置 下部柱 (182-191列处理)
Col_6F_L = [ ...
    Strain_Resampled(:, 182), ... % 右下角纵筋
    Strain_Resampled(:, 184), ... % 右上角纵筋
    Strain_Resampled(:, 187), ... % 左下角纵筋
    Strain_Resampled(:, 189), ... % 左上角纵筋
    Strain_Resampled(:, 190), ... % 箍筋(上下)
    Strain_Resampled(:, 191)  ... % 箍筋(左右)
];

% 拼接最终矩阵：共 6 * 6 + 3 * 6 = 54 列数据
Final_Data_Only = [Col_3F_U, Col_4F_L, Col_4F_U, Col_5F_L, Col_5F_U, Col_6F_L, Beam_4F_L, Beam_4F_R, Beam_5F_L, Beam_5F_R, Beam_6F_L, Beam_6F_R];

%% Excel 导出
excelDir = cfg.matlab_spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Rebar_Strain_' directory '.xlsx']);

t = (0:new_dt:new_dt*(size(Final_Data_Only,1)-1))';

% 定义精确表头 (共 1 + 54 = 55 项) 
header_names = {'Time_s', ...
    ... % 1. Col_3F_U (6列)
    'C3F_U_BR','C3F_U_TR','C3F_U_BL','C3F_U_TL','C3F_U_Stir_V','C3F_U_Stir_H', ...
    ... % 2. Col_4F_L (6列)
    'C4F_L_BR','C4F_L_TR','C4F_L_BL','C4F_L_TL','C4F_L_Stir_V','C4F_L_Stir_H', ...
    ... % 3. Col_4F_U (6列)
    'C4F_U_BR','C4F_U_TR','C4F_U_BL','C4F_U_TL','C4F_U_Stir_V','C4F_U_Stir_H', ...
    ... % 4. Col_5F_L (6列)
    'C5F_L_BR','C5F_L_TR','C5F_L_BL','C5F_L_TL','C5F_L_Stir_V','C5F_L_Stir_H', ...
    ... % 5. Col_5F_U (6列)
    'C5F_U_BR','C5F_U_TR','C5F_U_BL','C5F_U_TL','C5F_U_Stir_V','C5F_U_Stir_H', ...
    ... % 6. Col_6F_L (6列)
    'C6F_L_BR','C6F_L_TR','C6F_L_BL','C6F_L_TL','C6F_L_Stir_V','C6F_L_Stir_H', ...
    ... % 7. Beam_4F_L (3列)
    'B4F_L_TL','B4F_L_BL','B4F_L_Stir', ...
    ... % 8. Beam_4F_R (3列)
    'B4F_R_TL','B4F_R_BL','B4F_R_Stir', ...
    ... % 9. Beam_5F_L (3列)
    'B5F_L_TL','B5F_L_BL','B5F_L_Stir', ...
    ... % 10. Beam_5F_R (3列)
    'B5F_R_TL','B5F_R_BL','B5F_R_Stir', ...
    ... % 11. Beam_6F_L (3列)
    'B6F_L_TL','B6F_L_BL','B6F_L_Stir', ...
    ... % 12. Beam_6F_R (3列)
    'B6F_R_TL','B6F_R_BL','B6F_R_Stir'};

% 校验列数，防止 cell2table 报错
if length(header_names) ~= (size(Final_Data_Only, 2) + 1)
    error('错误：表头数量(%d)与数据总列数(%d)不匹配！请核对拼接逻辑。', length(header_names), size(Final_Data_Only, 2) + 1);
end

T_final = cell2table([num2cell(t), num2cell(Final_Data_Only)], 'VariableNames', header_names);
writetable(T_final, MasterFileName, 'Sheet', 'EssentialStrainData');

fprintf('>> 处理完成！\n');
