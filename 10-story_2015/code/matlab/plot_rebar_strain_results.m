function generatedFiles = plot_rebar_strain_results(statusInput, mode)
%PLOT_REBAR_STRAIN_RESULTS Plot only successfully completed strain results.
%   PLOT_REBAR_STRAIN_RESULTS() scans the standardized status directory.
%   PLOT_REBAR_STRAIN_RESULTS(STATUS_INPUT, MODE) accepts one status JSON
%   file or a directory containing *.status.json files. MODE is "paper"
%   or "ppt". The calculation script is never called by this function.

cfg = project_config();
addpath(cfg.common_plotting_dir);

if nargin < 1 || strlength(string(statusInput)) == 0
    statusInput = fullfile( ...
        cfg.spreadsheets_dir, ...
        'Strain_Grouped_75_104_180_184');
end
if nargin < 2
    mode = '';
end

plotStyle = plot_style(mode);
statusFiles = resolveStatusFiles(statusInput);
generatedFiles = {};

for statusIndex = 1:length(statusFiles)
    statusFilePath = statusFiles{statusIndex};
    statusInfo = jsondecode(fileread(statusFilePath));

    if ~isfield(statusInfo, 'status') || ~strcmp(statusInfo.status, 'completed')
        fprintf('跳过未成功结果：%s\n', statusFilePath);
        continue;
    end
    validateCompletedStatus(statusInfo, statusFilePath);

    resultData = readmatrix(statusInfo.dataFile, 'Sheet', statusInfo.sheet);
    if isempty(resultData) || size(resultData, 2) < 2
        error('plot_rebar_strain_results:InvalidData', ...
            '成功结果数据为空或列数不足：%s', statusInfo.dataFile);
    end

    outputTime = resultData(:, 1);
    if ~isfolder(statusInfo.outputImageDir)
        mkdir(statusInfo.outputImageDir);
    end

    for seriesIndex = 1:length(statusInfo.series)
        seriesInfo = statusInfo.series(seriesIndex);
        excelColumns = reshape(seriesInfo.excelColumns, 1, []);
        sourceColumns = reshape(seriesInfo.sourceDataColumns, 1, []);
        memberData = resultData(:, excelColumns);
        peakAmplitude = max(abs(memberData), [], 1);

        fig = figure('Visible', 'off');
        hold on;
        for lineIndex = 1:size(memberData, 2)
            plot( ...
                outputTime, ...
                memberData(:, lineIndex), ...
                'Color', seriesInfo.lineColors(lineIndex, :));
        end
        hold off;
        grid on;
        box on;

        xlabel('Time (s)', 'FontSize', plotStyle.fontLabel);
        ylabel('\epsilon/\epsilon_y', ...
            'Interpreter', 'tex', ...
            'FontSize', plotStyle.fontLabel);
        if plotStyle.showTitle
            title( ...
                sprintf('%s - %s', statusInfo.caseName, seriesInfo.memberName), ...
                'Interpreter', 'none', ...
                'FontSize', plotStyle.fontTitle);
        end

        legendText = cell(1, size(memberData, 2));
        for lineIndex = 1:size(memberData, 2)
            legendText{lineIndex} = sprintf( ...
                '%s (Col %d) | Amp. = %.3f', ...
                seriesInfo.legendNames{lineIndex}, ...
                sourceColumns(lineIndex), ...
                peakAmplitude(lineIndex));
        end
        legend(legendText, 'Location', 'best', 'Interpreter', 'none');

        xlim([statusInfo.startTime, statusInfo.endTime]);
        xticks(statusInfo.startTime:5:statusInfo.endTime);
        ylim([-2, 8]);
        yticks(-2:1:8);

        outputStem = fullfile( ...
            statusInfo.outputImageDir, ...
            sprintf('%s_%s', ...
            sanitizeFileName(statusInfo.caseName), ...
            seriesInfo.memberName));
        savedPaths = plotStyle.save(fig, outputStem);
        generatedFiles = [generatedFiles, savedPaths]; %#ok<AGROW>
        close(fig);
    end
end

fprintf('已从成功状态生成 %d 个正式图片文件。\n', length(generatedFiles));
end


function statusFiles = resolveStatusFiles(statusInput)
statusInput = char(string(statusInput));
if isfolder(statusInput)
    listing = dir(fullfile(statusInput, '*.status.json'));
    statusFiles = arrayfun( ...
        @(item) fullfile(item.folder, item.name), ...
        listing, ...
        'UniformOutput', false);
elseif isfile(statusInput)
    statusFiles = {statusInput};
else
    error('plot_rebar_strain_results:StatusNotFound', ...
        '找不到状态文件或目录：%s', statusInput);
end
end


function validateCompletedStatus(statusInfo, statusFilePath)
requiredFields = { ...
    'dataFile', ...
    'sheet', ...
    'outputImageDir', ...
    'startTime', ...
    'endTime', ...
    'series'};
for fieldIndex = 1:length(requiredFields)
    fieldName = requiredFields{fieldIndex};
    if ~isfield(statusInfo, fieldName)
        error('plot_rebar_strain_results:IncompleteStatus', ...
            '成功状态缺少字段 %s：%s', fieldName, statusFilePath);
    end
end
if ~isfile(statusInfo.dataFile)
    error('plot_rebar_strain_results:DataNotFound', ...
        '成功状态引用的数据文件不存在：%s', statusInfo.dataFile);
end
end


function safeName = sanitizeFileName(inputName)
safeName = char(string(inputName));
invalidChars = '<>:"/\|?*';
for charIndex = 1:length(invalidChars)
    safeName(safeName == invalidChars(charIndex)) = '_';
end
safeName = strtrim(safeName);
end
