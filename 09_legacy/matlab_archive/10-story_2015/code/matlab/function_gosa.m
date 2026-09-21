function [AccX_SE, AccX_NW, AccY_SE, AccY_NW] = function_gosa(AccX_SE,AccX_NW,AccY_SE,AccY_NW,nFloor,nData)

% ===============================================================
% function_gosa
% SE / NW 双侧加速度误差修正（E-Defense 2015 使用）
%
% 输入：
%   AccX_SE, AccX_NW : X方向 东南/西北角加速度矩阵（时间 × 层）
%   AccY_SE, AccY_NW : Y方向 东南/西北角加速度矩阵（时间 × 层）
%   nFloor           : 层数（= length(M)）
%   nData            : 数据点数（= length(AccX_SE)）
%
% 输出：
%   修正后的 SE/NW 加速度矩阵
%   若 SE 与 NW 差异大，则保留绝对值较小的一侧
% ===============================================================

for f = 1:nFloor   % 每一层
    for t = 1:nData   % 每个时间点
        
        %% --- X 方向误差处理 ---
        if abs(AccX_SE(t,f)) > abs(AccX_NW(t,f))
            % NW 更可靠 → 保留 NW
            AccX_SE(t,f) = AccX_NW(t,f);
        else
            % SE 更可靠
            AccX_NW(t,f) = AccX_SE(t,f);
        end

        %% --- Y 方向误差处理 ---
        if abs(AccY_SE(t,f)) > abs(AccY_NW(t,f))
            AccY_SE(t,f) = AccY_NW(t,f);
        else
            AccY_NW(t,f) = AccY_SE(t,f);
        end

    end
end

end
