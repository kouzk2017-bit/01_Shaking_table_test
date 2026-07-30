%% 初始化设置
clear; clc; close all;

dt = 1/1000;
new_dt = 1/100;
k = 20;
cutHHz = 50;
gosaThreshold = 1; % NW/SE差值超过1 m/s2时才执行异常值替换

%% 获取路径与元数据
cfg = project_config();

folder_list = readcell(cfg.folder_list_file);
directory   = char(string(folder_list{k,1}));
test_date   = char(string(folder_list{k,2}));
test_folder = char(string(folder_list{k,3}));
csv_prefix  = char(string(folder_list{k,4}));

txtdir = fullfile(cfg.processed_text_dir, test_date, test_folder);
if ~exist(txtdir, 'dir'), mkdir(txtdir); end

%% 数据读取
fprintf('>> 正在处理案例: %s\n', directory);
% 本脚本的楼层及台面加速度只使用JB7和JB13。
% 不再读取未参与计算、且部分工况不存在的JB15，避免文件缺失造成列号错位。
jb_list = [7 13];
CH_counts = {1:64, 1:64};

Acc_parts = cell(1, length(jb_list));
for j = 1:length(jb_list)
    jb_now = jb_list(j);
    csv_file = fullfile(cfg.raw_data_dir, test_date, test_folder, sprintf('%s%02d.csv', csv_prefix, jb_now));
    
    if ~isfile(csv_file)
        error('缺少必要的加速度文件: %s', csv_file);
    end

    opts = detectImportOptions(csv_file);
    opts.DataLines = [4 Inf];
    Tcsv = readtable(csv_file, opts);

    current_CHs = CH_counts{j};
    current_data = Tcsv{:, current_CHs + 1};
    Acc_parts{j} = current_data;

    for ch = current_CHs
        ch_data = current_data(:,ch);
        % 自动备份 TXT
        try writematrix(ch_data, fullfile(txtdir, sprintf('JB%d_CH%d.txt', jb_now, ch)), 'Delimiter', 'tab'); catch; end
    end
end

if numel(unique(cellfun(@(x) size(x,1), Acc_parts))) ~= 1
    error('JB7和JB13的数据点数不一致，无法按列合并。');
end
Acc_Raw = horzcat(Acc_parts{:});

if size(Acc_Raw,2) ~= 128
    error('通道数异常：应读取JB7和JB13共128个通道，实际为%d个。', size(Acc_Raw,2));
end

%% 建立原始时间轴
t_raw = (0:size(Acc_Raw,1)-1)' * dt;
Acc = Acc_Raw;

%% 提取楼层与各层响应数据 
% (JB7：1-12通道为1F-4F的NW位置xyz方向；16-36通道为5F-RF的NW位置xyz方向；43-45通道为TBL的NW位置xyz方向)
% (JB13：1-12通道为1F-4FD的SE位置xyz方向；19-39通道为5F-RF的SE位置xyz方向；46-48通道为TBL的SE位置xyz方向)
% (JB15：25-27通道为输入的xyz方向加速度)
% 单位m/s2

% 定义精确的通道索引
% NW 位置 (JB7)
idx_NW_1to4  = 1:12;   
idx_NW_5toRF = 16:36; 
idx_NW_TBL   = 43:45;
idx_NW_all   = [idx_NW_1to4, idx_NW_5toRF];

% SE 位置 (JB13)
idx_SE_1to4  = 65:76;  
idx_SE_5toRF = 83:103; 
idx_SE_TBL   = 110:112;
idx_SE_all   = [idx_SE_1to4, idx_SE_5toRF];

% 提取并分离各方向加速度 (1F 到 RF，共 11 层) ---
% NW 方向提取
AccX_NW = Acc(:, idx_NW_all(1:3:end)); % 提取 1, 4, 7... 列
AccY_NW = Acc(:, idx_NW_all(2:3:end)); % 提取 2, 5, 8... 列
AccZ_NW = Acc(:, idx_NW_all(3:3:end)); % 提取 3, 6, 9... 列

% SE 方向提取
AccX_SE = Acc(:, idx_SE_all(1:3:end));
AccY_SE = Acc(:, idx_SE_all(2:3:end));
AccZ_SE = Acc(:, idx_SE_all(3:3:end));

%% 按旧脚本修正2F~RF水平方向加速度
% 旧脚本参与惯性力计算的是2F~RF共10个质量点；1F加速度不参与层剪力计算。
AccX_NW_shear = AccX_NW(:,2:end);
AccY_NW_shear = AccY_NW(:,2:end);
AccX_SE_shear = AccX_SE(:,2:end);
AccY_SE_shear = AccY_SE(:,2:end);

[AccX_SE_shear, AccX_NW_shear, AccY_SE_shear, AccY_NW_shear] = ...
    function_gosa(AccX_SE_shear, AccX_NW_shear, ...
                  AccY_SE_shear, AccY_NW_shear, ...
                  10, size(AccX_SE_shear,1), gosaThreshold);

% 旧脚本对2019-0109-006-1（100%）约18.4~19.0 s进行专门修正，
% 并使用其10~30 s分析窗的末端值（即原始记录约30 s处）进行替换。
if strcmp(test_folder, '2019-0109-006-1')
    badIdx = t_raw >= 18.4 & t_raw <= 19.0;
    if any(badIdx)
        [~, refRow] = min(abs(t_raw - 30));
        AccX_SE_shear(badIdx,:) = repmat(AccX_SE_shear(refRow,:), sum(badIdx), 1);
        AccX_NW_shear(badIdx,:) = repmat(AccX_NW_shear(refRow,:), sum(badIdx), 1);
        AccY_SE_shear(badIdx,:) = repmat(AccY_SE_shear(refRow,:), sum(badIdx), 1);
        AccY_NW_shear(badIdx,:) = repmat(AccY_NW_shear(refRow,:), sum(badIdx), 1);
        fprintf('>> 已按旧脚本修正18.4~19.0 s异常加速度，共%d个采样点。\n', sum(badIdx));
    else
        warning('原始记录中没有找到18.4~19.0 s异常段。');
    end
end

% 将修正后的2F~RF数据放回完整的1F~RF矩阵，供Excel导出。
AccX_NW(:,2:end) = AccX_NW_shear;
AccY_NW(:,2:end) = AccY_NW_shear;
AccX_SE(:,2:end) = AccX_SE_shear;
AccY_SE(:,2:end) = AccY_SE_shear;

% 合成各楼层中心位置加速度 (11层均值)
Accx_full = (AccX_SE + AccX_NW) / 2; 
Accy_full = (AccY_SE + AccY_NW) / 2;
Accz_full = (AccZ_SE + AccZ_NW) / 2;

% 提取振动台台面 (TBL) 响应数据 (取 NW 与 SE 均值)
Acc_TBL_NW = Acc(:, idx_NW_TBL);
Acc_TBL_SE = Acc(:, idx_SE_TBL);
Acc_TBL_Response = (Acc_TBL_NW + Acc_TBL_SE) / 2;

%% 定义质量向量 (单位: t)
g = 9.81;

mR  = 579/g;       % [kN/(m/s2)] = [t]
m10 = (706+57)/g;
m9  = (639+28)/g;
m8  = (657+28)/g;
m7  = (721+29)/g;
m6  = (870+188)/g;
m5  = (716+28)/g;
m4  = (732+28)/g;
m3  = (750+28)/g;
m2  = (848+57)/g;

% 2F~RF质量向量（1x10）
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
ShearFx_raw = flip(cumsum(flip(Fx, 2), 2), 2);
ShearFy_raw = flip(cumsum(flip(Fy, 2), 2), 2);

% 与旧脚本一致：先求层剪力，再以原采样率做50 Hz FFT低通。
ShearFx = Fn_filtering(ShearFx_raw, 1/dt, cutHHz, 'fft_LPF');
ShearFy = Fn_filtering(ShearFy_raw, 1/dt, cutHHz, 'fft_LPF');

%% 统一重采样至100 Hz，与层间位移角数据的时间轴一致
Accx_full = Fn_Resampling(Accx_full, dt, new_dt);
Accy_full = Fn_Resampling(Accy_full, dt, new_dt);
Accz_full = Fn_Resampling(Accz_full, dt, new_dt);
Acc_TBL_Response = Fn_Resampling(Acc_TBL_Response, dt, new_dt);
ShearFx = Fn_Resampling(ShearFx, dt, new_dt);
ShearFy = Fn_Resampling(ShearFy, dt, new_dt);

t = (0:size(Accx_full,1)-1)' * new_dt;

%% 提取最大值 (用于设计或分析)
Max_ShearX = max(abs(ShearFx), [], 1);
Max_ShearY = max(abs(ShearFy), [], 1);

fprintf('>> 层剪力计算完成。1F最大剪力: %.2f kN\n', Max_ShearX(1));
%% Excel 导出
excelDir = cfg.matlab_spreadsheets_dir;
if ~exist(excelDir, 'dir'), mkdir(excelDir); end
MasterFileName = fullfile(excelDir, ['Acceleration_' directory '.xlsx']);

% writetable写入较短数据时不会清除旧工作表尾部的残留行。
% 因此先删除本工况同名旧结果，再从空工作簿重新创建。
if isfile(MasterFileName)
    delete(MasterFileName);
end

% --- 表头定义 ---
header_acc = [{'Time_s'}, arrayfun(@(i) sprintf('%dF_m/s2', i), 1:10, 'UniformOutput', false), {'RF_m/s2'}];
header_shear = [{'Time_s'}, arrayfun(@(i) sprintf('%dF_kN', i), 1:10, 'UniformOutput', false)];
header_tbl = {'Time_s', 'TBL_X_m/s2', 'TBL_Y_m/s2', 'TBL_Z_m/s2'};

% --- 写入数据 ---
write_tab = @(data, header, sheet) writetable(cell2table([num2cell(t), num2cell(data)], 'VariableNames', header), MasterFileName, 'Sheet', sheet);

write_tab(Accx_full, header_acc, 'Accx');
write_tab(Accy_full, header_acc, 'Accy');
write_tab(Accz_full, header_acc, 'Accz');
write_tab(ShearFx, header_shear, 'ShearFx');
write_tab(ShearFy, header_shear, 'ShearFy');
write_tab(Acc_TBL_Response, header_tbl, 'TBL_Response');

fprintf('>>> 处理完成！\nExcel 保存于: %s\n', MasterFileName);
