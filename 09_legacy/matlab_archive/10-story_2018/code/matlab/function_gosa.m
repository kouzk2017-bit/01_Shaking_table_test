function [AccX_SE, AccX_NW, AccY_SE, AccY_NW] = function_gosa( ...
    AccX_SE, AccX_NW, AccY_SE, AccY_NW, nFloor, nData, gosa)

% ===============================================================
% function_gosa
% SE / NW 双侧加速度误差修正（E-Defense 2015 使用）
%
% 输入：
%   AccX_SE, AccX_NW : X方向 东南/西北角加速度矩阵（时间 × 层）
%   AccY_SE, AccY_NW : Y方向 东南/西北角加速度矩阵（时间 × 层）
%   nFloor           : 层数（= length(M)）
%   nData            : 数据点数（= size(AccX_SE,1)）
%   gosa             : NW/SE差值阈值，默认1 m/s2
%
% 输出：
%   修正后的 SE/NW 加速度矩阵
%   仅当SE与NW之差超过gosa时，才保留绝对值较小的一侧
% ===============================================================

if nargin < 7 || isempty(gosa)
    gosa = 1;
end

if nFloor > min([size(AccX_SE,2), size(AccX_NW,2), ...
                 size(AccY_SE,2), size(AccY_NW,2)])
    error('nFloor超过输入加速度矩阵的列数。');
end
if nData > min([size(AccX_SE,1), size(AccX_NW,1), ...
                size(AccY_SE,1), size(AccY_NW,1)])
    error('nData超过输入加速度矩阵的行数。');
end

rows = 1:nData;
cols = 1:nFloor;

% X方向：只有两侧差值超过阈值时，才用绝对值较小的一侧替换较大值。
xSE = AccX_SE(rows,cols);
xNW = AccX_NW(rows,cols);
xDiffLarge = abs(xSE - xNW) > gosa;
replaceSE = xDiffLarge & abs(xSE) > abs(xNW);
replaceNW = xDiffLarge & abs(xNW) > abs(xSE);
xSE(replaceSE) = xNW(replaceSE);
xNW(replaceNW) = xSE(replaceNW);
AccX_SE(rows,cols) = xSE;
AccX_NW(rows,cols) = xNW;

% Y方向采用相同逻辑。
ySE = AccY_SE(rows,cols);
yNW = AccY_NW(rows,cols);
yDiffLarge = abs(ySE - yNW) > gosa;
replaceSE = yDiffLarge & abs(ySE) > abs(yNW);
replaceNW = yDiffLarge & abs(yNW) > abs(ySE);
ySE(replaceSE) = yNW(replaceSE);
yNW(replaceNW) = ySE(replaceNW);
AccY_SE(rows,cols) = ySE;
AccY_NW(rows,cols) = yNW;

end
