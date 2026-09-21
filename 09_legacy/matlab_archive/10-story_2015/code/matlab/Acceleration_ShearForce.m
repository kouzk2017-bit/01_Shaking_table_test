%% 初始化设置
clear; clc; close all;

new_dt = 1/100;       
dt = 1/1000;          
k = 10;               
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

%% 数据读取（JB13为1层-10层加速度；JB14：1-6通道为顶层加速度，7-9通道为SW位置xyz方向的振动台响应速度；JB15：25-27通道为输入加速度）
fprintf('>> 正在处理案例: %s\n', directory);
jb_list = [13 14 15];
CH_counts = {1:60, 1:21, 1:64}; 

Acc_Raw = [];
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
            Acc_Raw(:, end+1) = ch_data; 
            % 自动备份 TXT
            try writematrix(ch_data, fullfile(txtdir, sprintf('JB%d_CH%d.txt', jb_now, ch)), 'Delimiter', 'tab'); catch; end
        end
    end
end

%% 信号处理
acc_filtered = Fn_filtering(Acc_Raw, 1/dt, [cutLHz cutHHz], 'fft_BPF');
Acc = Fn_Resampling(acc_filtered, dt, new_dt);

%% 提取楼层与各层响应数据 (1F-10F, RF)
% 单位m/s2
% 分离各方向加速度 (1F 到 RF，共 11 层)
AccX_SE = Acc(:, 1:6:61);  AccX_NW = Acc(:, 4:6:64);
AccY_SE = Acc(:, 2:6:62);  AccY_NW = Acc(:, 5:6:65);
AccZ_SE = Acc(:, 3:6:63);  AccZ_NW = Acc(:, 6:6:66);

% 基础板BF1原始测点数据提取
% 通道对应关系：73=BF1-AX-SW、74=BF1-AY-SW、75=BF1-AZ-SW、76=BF1-AX-NW、77=BF1-AY-NW、78=BF1-AZ-NW
BF1_Raw = Acc(:, 73:78);
BF1_X_SW = BF1_Raw(:,1); BF1_Y_SW = BF1_Raw(:,2); BF1_Z_SW = BF1_Raw(:,3);
BF1_X_NW = BF1_Raw(:,4); BF1_Y_NW = BF1_Raw(:,5); BF1_Z_NW = BF1_Raw(:,6);

% 误差修正处理 (使用你提供的 function_gosa)
[AccX_SE, AccX_NW, AccY_SE, AccY_NW] = function_gosa(AccX_SE, AccX_NW, AccY_SE, AccY_NW, 10, size(AccX_SE,1));
% 新增：BF1基础板X/Y向加速度修正（Z向不修正，与楼层处理逻辑统一）
[BF1_X_SW, BF1_X_NW, BF1_Y_SW, BF1_Y_NW] = function_gosa(BF1_X_SW, BF1_X_NW, BF1_Y_SW, BF1_Y_NW, 1, size(BF1_X_SW,1));

% 合成各楼层中心位置的加速度 (SE与NW取平均)
% 结果为 11 列矩阵，对应 [1F, 2F, 3F, 4F, 5F, 6F, 7F, 8F, 9F, 10F, RF]
Accx_full = (AccX_SE + AccX_NW) / 2; 
Accy_full = (AccY_SE + AccY_NW) / 2;
Accz_full = (AccZ_SE + AccZ_NW) / 2;

% 基础板加速度合成
% BF1基础板中心加速度（SW与NW双测点取平均，与楼层逻辑一致）
Accx_BF1 = (BF1_X_SW + BF1_X_NW) / 2;
Accy_BF1 = (BF1_Y_SW + BF1_Y_NW) / 2;
Accz_BF1 = (BF1_Z_SW + BF1_Z_NW) / 2;

% BF2基础板加速度（仅单测点，无需取平均，通道对应79=AX、80=AY、81=AZ）
BF2_Raw = Acc(:, 79:81);
Accx_BF2 = BF2_Raw(:,1);
Accy_BF2 = BF2_Raw(:,2);
Accz_BF2 = BF2_Raw(:,3);

% 提取振动台台面响应加速度
Acc_TBL_Response = Acc(:, 67:69);

%% 定义质量向量 (单位: t)
g = 9.8; % 重力加速度

mR = 725/9.8;   %[kN/m/s2]=[t]
m10 = (740+57)/9.8;
m9  = (694+28)/9.8;
m8  = (716+28)/9.8;
m7  = (949+28)/9.8;
m6  = (618+188)/9.8;
m5  = (780+28)/9.8;
m4  = (798+28)/9.8;
m3  = (817+28)/9.8;
m2  = (889+57)/9.8;

% 组成质量向量 (1x11)
M = [m2, m3, m4, m5, m6, m7, m8, m9, m10, mR];

%% 计算惯性力与层剪力 (Vectorized)
% 物理公式: F = -m * a

% 1. 计算各层每一时刻的惯性力 [kN]
% 使用 .* 确保每一列加速度乘以其对应楼层的质量
Fx = -Accx_full(:,2:end) .* M; 
Fy = -Accy_full(:,2:end) .* M;

% 2. 计算层剪力 [kN]
% 逻辑：从顶层(RF)向底层(1F)累加过程
% flip(..., 2) 将 [1F...RF] 翻转为 [RF...1F]
% cumsum 累加得到剪力
% 再次 flip 翻转回 [1F...RF] 的顺序
ShearFx = flip(cumsum(flip(Fx, 2), 2), 2);
ShearFy = flip(cumsum(flip(Fy, 2), 2), 2);

%% 提取最大值 (用于设计或分析)
Max_ShearX = max(abs(ShearFx)); % 每一层在整个时间段内的最大剪力
Max_ShearY = max(abs(ShearFy));

fprintf('>> 层剪力计算完成。1F最大剪力: %.2f kN\n', Max_ShearX(1));
%% Excel 导出
excelDir = cfg.spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Acceleration_' regexprep(directory, '[^\w]', '_') '.xlsx']);

t = (0:new_dt:new_dt*(size(Accx_full,1)-1))';

% --- 表头定义 ---
header_acc = [{'Time_s'}, arrayfun(@(i) sprintf('%dF_m/s2', i), 1:10, 'UniformOutput', false), {'RF_m/s2'}];
header_shear = [{'Time_s'}, arrayfun(@(i) sprintf('%dF_kN', i), 2:10, 'UniformOutput', false), {'RF_kN'}];
header_tbl = {'Time_s', 'TBL_X_m/s2', 'TBL_Y_m/s2', 'TBL_Z_m/s2'};
header_BF = {'Time_s', 'X_m/s2', 'Y_m/s2', 'Z_m/s2'};

% --- 写入数据 ---
write_tab = @(data, header, sheet) writetable(cell2table([num2cell(t), num2cell(data)], 'VariableNames', header), MasterFileName, 'Sheet', sheet);

write_tab(Accx_full, header_acc, 'Accx');
write_tab(Accy_full, header_acc, 'Accy');
write_tab(Accz_full, header_acc, 'Accz');
write_tab(ShearFx, header_shear, 'ShearFx');
write_tab(ShearFy, header_shear, 'ShearFy');
write_tab(Acc_TBL_Response, header_tbl, 'TBL_Response');
write_tab([Accx_BF1, Accy_BF1, Accz_BF1], header_BF, 'Acc_BF1');
write_tab([Accx_BF2, Accy_BF2, Accz_BF2], header_BF, 'Acc_BF2');

fprintf('>>> 处理完成！\nExcel 保存于: %s\n', MasterFileName);
