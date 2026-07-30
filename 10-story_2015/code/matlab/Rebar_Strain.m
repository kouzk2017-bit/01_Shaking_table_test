%% 初始化设置
clear;
clc;
close all;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 振动台试验钢筋应变数据处理
%
% 数据流程：
% 原始CSV
%   ↓
% 分通道生成TXT
%   ↓
% 从TXT重新读取
%   ↓
% 检查并统一各通道长度
%   ↓
% 严格连续继承前一正式加载工况残余应变
%   ↓
% 1000 Hz重采样到100 Hz
%   ↓
% 截取10～30 s
%   ↓
% 应变除以2000
%   ↓
% 仅提取完整数据矩阵第103～107列
%   ↓
% 自动覆盖旧Excel并写出独立状态文件
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%% 1. 基本参数

dt     = 1/1000;          % 原始采样间隔，1000 Hz
new_dt = 1/100;           % 重采样间隔，100 Hz

startTime = 10;           % 输出起始时间，s
endTime   = 30;           % 输出结束时间，s

baselineDuration = 1.0;   % 当前工况起始稳定段平均时长，s
residualDuration = 1.0;   % 当前工况结束稳定段平均时长，s

strain_y = 2000;          % 屈服应变/归一化除数，με
minAmplitude = [];           % 当前版本不按幅值筛选，全部输出指定列（保留变量仅为兼容）

% 正式加载工况，按试验时间顺序排列
kList = [2, 4, 7, 10, 13, 15, 17, 20];

% target保留，但当前不参与数据处理
targetList = [ ...
    NaN, NaN, NaN, NaN, ...
    NaN, NaN, NaN, NaN];

% 示例：
% targetList = [1/200, 1/100, 1/75, 1/50, ...
%               1/200, 1/100, 1/75, 1/50];


%% 2. JB与通道设置

jb_list = [4, 5, 6, 16];

CH_counts = { ...
    1:52, ...     % JB04
    1:50, ...     % JB05
    1:62, ...     % JB06
    1:22};        % JB16

totalChannels = 52 + 50 + 62 + 22;    % 186个通道


%% 3. 获取主路径

cfg = project_config();
folderListFile = cfg.folder_list_file;

if ~isfile(folderListFile)
    error('找不到folder_list.xlsx：\n%s', folderListFile);
end

[~, folder_list] = xlsread(folderListFile);

if size(folder_list, 2) < 4
    error([ ...
        'folder_list.xlsx至少需要4列：\n', ...
        '第1列：工况名称\n', ...
        '第2列：试验日期\n', ...
        '第3列：试验文件夹\n', ...
        '第4列：CSV文件前缀']);
end


%% 4. 输出目录

excelRootDir = fullfile( ...
    cfg.spreadsheets_dir, ...
    'Strain_Grouped_75_104_180_184');

if ~exist(excelRootDir, 'dir')
    mkdir(excelRootDir);
end


%% 5. 定义需要提取的构件和外侧测点
%
% 完整临时数据矩阵：
%
% 第1列：时间
% 第2～187列：186个钢筋应变通道
%
% 以下dataColumns均为包含时间列后的实际列号。
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

members = struct( ...
    'memberName', {}, ...
    'dataColumns', {}, ...
    'outputNames', {}, ...
    'legendNames', {}, ...
    'lineColors', {});


%% 5.2 提取并组合输出指定列（英文标注）
% Group 1: 4F -> Columns 44 & 105
members(end+1).memberName = '4F';
members(end).dataColumns = [44, 105];
members(end).outputNames = {'Figure_4F'};
members(end).legendNames = {'4F Beam Longitudinal Rebar', '4F Column Longitudinal Rebar'};
members(end).lineColors = {[1, 0, 0], [0, 0, 1]};   % Beam: red, Column: blue

% Group 2: 6F -> Columns 179 & 185
members(end+1).memberName = '6F';
members(end).dataColumns = [179, 185];
members(end).outputNames = {'Figure_6F'};
members(end).legendNames = {'6F Beam Longitudinal Rebar', '6F Column Longitudinal Rebar'};
members(end).lineColors = {[1, 0, 0], [0, 0, 1]};   % Beam: red, Column: blue


%% 6. 初始化上一正式加载工况残余应变

previousResidual = zeros(1, totalChannels);


%% 7. 依次处理全部正式加载工况

for caseIndex = 1:length(kList)

    k = kList(caseIndex);
    target = targetList(caseIndex);

    fprintf('\n====================================================\n');
    fprintf('>> 正在处理正式加载工况 k = %d\n', k);

    if ~isnan(target)
        fprintf('>> target = %.8f\n', target);
    end


    %% 8.1 获取当前工况元数据

    if k > size(folder_list, 1)
        error('k=%d超过folder_list.xlsx有效行数。', k);
    end

    directory   = cellToText(folder_list{k, 1});
    test_date   = cellToText(folder_list{k, 2});
    test_folder = cellToText(folder_list{k, 3});
    csv_prefix  = cellToText(folder_list{k, 4});

    if strlength(directory) == 0
        error('folder_list.xlsx第%d行第1列为空。', k);
    end

    if strlength(test_date) == 0
        error('folder_list.xlsx第%d行第2列为空。', k);
    end

    if strlength(test_folder) == 0
        error('folder_list.xlsx第%d行第3列为空。', k);
    end

    if strlength(csv_prefix) == 0
        error('folder_list.xlsx第%d行第4列为空。', k);
    end

    safeDirectoryName = sanitizeFileName(directory);
    statusFilePath = fullfile( ...
        excelRootDir, ...
        sprintf('Strain_Grouped_75_104_180_184_%s.status.json', ...
        safeDirectoryName));

    statusInfo = struct( ...
        'status', 'running', ...
        'analysis', 'rebar_strain', ...
        'caseName', char(directory), ...
        'testDate', char(test_date), ...
        'testFolder', char(test_folder), ...
        'startedUtc', utcTimestamp());
    writeStatusFile(statusFilePath, statusInfo);


    %% 8.2 当前工况路径

    rawCsvDir = fullfile( ...
        cfg.raw_data_dir, ...
        char(test_date), ...
        char(test_folder));

    txtdir = fullfile( ...
        cfg.processed_text_dir, ...
        char(test_date), ...
        char(test_folder));

    if ~exist(rawCsvDir, 'dir')
        error('找不到原始CSV目录：\n%s', rawCsvDir);
    end

    if ~exist(txtdir, 'dir')
        mkdir(txtdir);
    end

    fprintf('>> CSV目录：%s\n', rawCsvDir);
    fprintf('>> TXT目录：%s\n', txtdir);


    %% 8.3 从CSV生成TXT（若TXT已存在则直接跳过）

    allTxtExist = true;

    for j = 1:length(jb_list)

        jb_now = jb_list(j);
        current_CHs = CH_counts{j};

        for ch = current_CHs

            txt_file = fullfile( ...
                txtdir, ...
                sprintf('JB%02d_CH%d.txt', jb_now, ch));

            if ~isfile(txt_file)
                allTxtExist = false;
                break;
            end

        end

        if ~allTxtExist
            break;
        end

    end

    if allTxtExist

        fprintf('>> 检测到TXT文件已存在，跳过CSV转TXT，直接读取。\n');

    else

        fprintf('>> TXT文件不完整，正在从CSV生成TXT文件……\n');

        for j = 1:length(jb_list)

            jb_now = jb_list(j);

            csv_file = fullfile( ...
                rawCsvDir, ...
                sprintf('%s%02d.csv', char(csv_prefix), jb_now));

            if ~isfile(csv_file)
                error('找不到CSV文件：\n%s', csv_file);
            end

            opts = detectImportOptions(csv_file);
            opts.DataLines = [4, Inf];

            Tcsv = readtable(csv_file, opts);

            current_CHs = CH_counts{j};

            requiredCsvColumn = max(current_CHs) + 1;

            if width(Tcsv) < requiredCsvColumn
                error([ ...
                    'CSV列数不足：\n%s\n', ...
                    '实际列数：%d\n', ...
                    '至少需要：%d'], ...
                    csv_file, ...
                    width(Tcsv), ...
                    requiredCsvColumn);
            end

            for ch = current_CHs

                ch_data = Tcsv{:, ch + 1};

                if ~isnumeric(ch_data)
                    ch_data = str2double(string(ch_data));
                end

                ch_data = ch_data(:);

                % 只删除末尾空行或NaN。
                % 不删除时程中间的NaN，避免数据时间错位。
                lastValidIndex = find(~isnan(ch_data), 1, 'last');

                if isempty(lastValidIndex)
                    error([ ...
                        'CSV通道没有有效数据：\n', ...
                        'JB%02d_CH%d\n%s'], ...
                        jb_now, ch, csv_file);
                end

                ch_data = ch_data(1:lastValidIndex);

                txt_file = fullfile( ...
                    txtdir, ...
                    sprintf('JB%02d_CH%d.txt', jb_now, ch));

                writematrix( ...
                    ch_data, ...
                    txt_file, ...
                    'Delimiter', 'tab');

            end

            fprintf('   JB%02d：生成%d个TXT文件。\n', ...
                jb_now, length(current_CHs));

        end

    end


    %% 8.4 从TXT读取全部通道
    %
    % 先分别保存到cell。
    % 读取完全部186个通道后，再检查所有长度。
    % 如果个别通道多1行或少1行，则统一截取到最短长度。

    fprintf('>> 正在从TXT读取钢筋应变数据……\n');

    strainCell = cell(1, totalChannels);

    channelLengths = zeros(1, totalChannels);
    channelFileNames = strings(1, totalChannels);

    globalChannel = 0;

    for j = 1:length(jb_list)

        jb_now = jb_list(j);
        current_CHs = CH_counts{j};

        for ch = current_CHs

            globalChannel = globalChannel + 1;

            txt_file = fullfile( ...
                txtdir, ...
                sprintf('JB%02d_CH%d.txt', jb_now, ch));

            if ~isfile(txt_file)
                error('找不到TXT文件：\n%s', txt_file);
            end

            strainData = readmatrix(txt_file);
            strainData = strainData(:);

            % 只删除TXT末尾空行形成的NaN
            lastValidIndex = find(~isnan(strainData), 1, 'last');

            if isempty(lastValidIndex)
                error('TXT文件中没有有效数值：\n%s', txt_file);
            end

            strainData = strainData(1:lastValidIndex);

            strainCell{globalChannel} = strainData;

            channelLengths(globalChannel) = length(strainData);
            channelFileNames(globalChannel) = string(txt_file);

        end
    end

    if globalChannel ~= totalChannels
        error('通道数错误：实际%d，预期%d。', ...
            globalChannel, totalChannels);
    end


    %% 8.5 检查所有TXT长度

    minimumLength = min(channelLengths);
    maximumLength = max(channelLengths);

    fprintf('>> 最短通道长度：%d\n', minimumLength);
    fprintf('>> 最长通道长度：%d\n', maximumLength);

    if maximumLength ~= minimumLength

        fprintf([ ...
            '>> 检测到通道长度不一致。\n', ...
            '>> 最大相差：%d个采样点。\n', ...
            '>> 所有通道将统一截取到最短长度：%d。\n'], ...
            maximumLength - minimumLength, ...
            minimumLength);

        % 输出所有长度不同于最短长度的通道
        differentIndex = find(channelLengths ~= minimumLength);

        fprintf('>> 以下通道长度较长：\n');

        for idx = differentIndex

            fprintf('   %d 点：%s\n', ...
                channelLengths(idx), ...
                channelFileNames(idx));

        end

    else

        fprintf('>> 所有TXT通道长度一致。\n');

    end


    %% 8.6 建立统一长度的原始应变矩阵

    StrainRaw = zeros(minimumLength, totalChannels);

    for channelIndex = 1:totalChannels

        strainData = strainCell{channelIndex};

        % 统一截取到最短通道长度
        strainData = strainData(1:minimumLength);

        % 检查时程中间是否存在NaN
        if any(isnan(strainData))

            nanCount = sum(isnan(strainData));

            warning([ ...
                '第%d个通道时程中存在%d个NaN，', ...
                '使用线性插值补齐。'], ...
                channelIndex, nanCount);

            strainData = fillmissing( ...
                strainData, ...
                'linear', ...
                'EndValues', 'nearest');

        end

        % 使用当前工况起始稳定段的平均值进行基线修正，
        % 再叠加上一正式加载工况的残余应变。
        % 相比直接使用第一个采样点，可降低瞬时噪声影响。
        baselinePointCount = min( ...
            round(baselineDuration / dt), ...
            length(strainData));

        initialBaseline = mean( ...
            strainData(1:baselinePointCount), ...
            'omitnan');

        strainData = ...
            strainData - initialBaseline ...
            + previousResidual(channelIndex);

        StrainRaw(:, channelIndex) = strainData;

    end

    fprintf('>> 已读取%d个通道，统一长度为%d个点。\n', ...
        totalChannels, minimumLength);


    %% 8.7 重采样：1000 Hz → 100 Hz

    if exist('Fn_Resampling', 'file') ~= 2
        error([ ...
            '找不到Fn_Resampling.m。\n', ...
            '请确认函数位于当前MATLAB目录或已加入路径。']);
    end

    Strain = Fn_Resampling( ...
        StrainRaw, ...
        dt, ...
        new_dt);

    numberOfPoints = size(Strain, 1);

    t = (0:numberOfPoints-1)' * new_dt;

    fprintf('>> 重采样完成：1000 Hz → 100 Hz，共%d个点。\n', ...
        numberOfPoints);


    %% 8.8 保存当前工况残余应变
    %
    % 使用当前工况结束稳定段的平均值作为残余应变，
    % 避免直接取最后一个采样点时受到瞬时噪声影响。

    residualPointCount = min( ...
        round(residualDuration / new_dt), ...
        size(Strain, 1));

    previousResidual = mean( ...
        Strain(end-residualPointCount+1:end, :), ...
        1, ...
        'omitnan');


    %% 8.9 截取10～30秒

    timeIndex = ...
        t >= startTime & ...
        t <= endTime;

    if ~any(timeIndex)

        error([ ...
            'k=%d的数据不包含%.1f～%.1f s。\n', ...
            '当前总时长约为%.3f s。'], ...
            k, ...
            startTime, ...
            endTime, ...
            t(end));

    end

    outputTime = t(timeIndex);
    outputStrain = Strain(timeIndex, :);


    %% 8.10 应变除以2000

    outputStrain = outputStrain / strain_y;


    %% 8.11 建立完整临时数据矩阵
    %
    % 第1列：时间
    % 第2～187列：186个应变通道

    completeData = [outputTime, outputStrain];

    if size(completeData, 2) ~= totalChannels + 1
        error('完整数据矩阵列数错误。');
    end


    %% 8.12 提取指定测点
    %
    % 当前版本不按照幅值筛选。
    % 仅提取完整数据矩阵中的两组列，供独立绘图脚本读取。

    selectedData = outputTime;
    selectedHeaders = {'Time_s'};

    for memberIndex = 1:length(members)

        member = members(memberIndex);

        if any(member.dataColumns > size(completeData, 2))
            error('%s所需列超过数据范围。', member.memberName);
        end

        memberData = completeData(:, member.dataColumns);
        peakAmplitude = max(abs(memberData), [], 1);

        fprintf('\n>> %s：输出%d列。\n', ...
            member.memberName, ...
            length(member.dataColumns));

        for candidateIndex = 1:length(member.dataColumns)

            fprintf('   完整数据第%d列：幅值 = %.6f\n', ...
                member.dataColumns(candidateIndex), ...
                peakAmplitude(candidateIndex));

        end

        selectedData = [selectedData, memberData]; %#ok<AGROW>

        headersWithColumn = cell(1, length(member.outputNames));

        for headerIndex = 1:length(member.outputNames)

            headersWithColumn{headerIndex} = sprintf( ...
                '%s_Col%d', ...
                member.legendNames{headerIndex}, ...
                member.dataColumns(headerIndex));

        end

        selectedHeaders = [selectedHeaders, headersWithColumn]; %#ok<AGROW>


    end


    %% 8.14 输出最终Excel

    excelFileName = sprintf( ...
        'Strain_Grouped_75_104_180_184_%s.xlsx', ...
        safeDirectoryName);

    excelFilePath = fullfile( ...
        excelRootDir, ...
        excelFileName);

    if isfile(excelFilePath)
        delete(excelFilePath);
    end

    % 表头单独写入，防止中文和连字符被MATLAB修改
    writecell( ...
        selectedHeaders, ...
        excelFilePath, ...
        'Sheet', 'ExternalStrain', ...
        'Range', 'A1');

    writematrix( ...
        selectedData, ...
        excelFilePath, ...
        'Sheet', 'ExternalStrain', ...
        'Range', 'A2');

    outputImageDir = fullfile( ...
        cfg.figures_dir, ...
        char(test_date), ...
        char(test_folder), ...
        'Strain_Grouped_75_104_180_184');

    series = struct( ...
        'memberName', {}, ...
        'excelColumns', {}, ...
        'sourceDataColumns', {}, ...
        'legendNames', {}, ...
        'lineColors', {});
    nextExcelColumn = 2;
    for memberIndex = 1:length(members)
        series(memberIndex).memberName = members(memberIndex).memberName;
        series(memberIndex).excelColumns = ...
            nextExcelColumn:(nextExcelColumn + length(members(memberIndex).dataColumns) - 1);
        series(memberIndex).sourceDataColumns = members(memberIndex).dataColumns;
        series(memberIndex).legendNames = members(memberIndex).legendNames;
        series(memberIndex).lineColors = vertcat(members(memberIndex).lineColors{:});
        nextExcelColumn = nextExcelColumn + length(members(memberIndex).dataColumns);
    end

    statusInfo.status = 'completed';
    statusInfo.completedUtc = utcTimestamp();
    statusInfo.dataFile = excelFilePath;
    statusInfo.sheet = 'ExternalStrain';
    statusInfo.outputImageDir = outputImageDir;
    statusInfo.startTime = startTime;
    statusInfo.endTime = endTime;
    statusInfo.series = series;
    writeStatusFile(statusFilePath, statusInfo);

    fprintf('>>> 最终Excel已保存：\n%s\n', excelFilePath);
    fprintf('>>> 完成状态已保存：\n%s\n', statusFilePath);
    fprintf('>>> 输出时间范围：%.2f～%.2f s\n', ...
        outputTime(1), outputTime(end));
    fprintf('>>> Excel尺寸：%d行 × %d列\n', ...
        size(selectedData, 1), ...
        size(selectedData, 2));

end


%% 8. 全部完成

fprintf('\n====================================================\n');
fprintf('>>> 全部正式加载工况处理完成。\n');
fprintf('>>> Excel总目录：\n%s\n', excelRootDir);
fprintf('>>> 正式图片请运行 plot_rebar_strain_results。\n');


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 局部函数1：将folder_list内容转换为字符串
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function textValue = cellToText(cellValue)

    if isempty(cellValue)
        textValue = "";
        return;
    end

    if ischar(cellValue)

        textValue = string(cellValue);

    elseif isstring(cellValue)

        textValue = cellValue;

    elseif isnumeric(cellValue)

        if isnan(cellValue)
            textValue = "";
        else
            textValue = string(cellValue);
        end

    elseif isdatetime(cellValue)

        textValue = string(cellValue, 'yyyyMMdd');

    else

        textValue = string(cellValue);

    end

    textValue = strtrim(textValue);

end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 局部函数2：根据逻辑值返回文本
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function outputText = ternaryText(conditionValue, trueText, falseText)

    if conditionValue
        outputText = trueText;
    else
        outputText = falseText;
    end

end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 局部函数3：清理文件名非法字符
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function safeName = sanitizeFileName(inputName)

    safeName = char(string(inputName));

    safeName = regexprep( ...
        safeName, ...
        '[<>:"/\\|?*]', ...
        '_');

    safeName = regexprep( ...
        safeName, ...
        '\s+', ...
        '_');

    safeName = regexprep( ...
        safeName, ...
        '_+', ...
        '_');

    safeName = strtrim(safeName);

end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 局部函数4：生成UTC时间戳
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function timestamp = utcTimestamp()

    timestamp = char(datetime( ...
        'now', ...
        'TimeZone', 'UTC', ...
        'Format', 'yyyy-MM-dd''T''HH:mm:ssXXX'));

end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 局部函数5：原子更新状态文件
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function writeStatusFile(statusFilePath, statusInfo)

    temporaryPath = [statusFilePath, '.tmp'];
    fileIdentifier = fopen(temporaryPath, 'w', 'n', 'UTF-8');
    if fileIdentifier < 0
        error('无法写入状态文件：\n%s', temporaryPath);
    end

    cleanupObject = onCleanup(@() fclose(fileIdentifier)); %#ok<NASGU>
    fprintf(fileIdentifier, '%s', jsonencode(statusInfo, 'PrettyPrint', true));
    clear cleanupObject;
    movefile(temporaryPath, statusFilePath, 'f');

end
