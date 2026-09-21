function [filtered] = Fn_filtering(data, data_freq, param,type)
% フィルタリング関数
% FFTによるLPF(200Hz)の例
% filtered = filtering(data,1000.0,200.0);
% FFTによるHPF(0.1Hz)の例
% filtered = filtering(data,1000.0,0.1,'fft_HPF');
% FFTによるBPF(0.1Hz-200Hz)の例
% filtered = filtering(data,1000.0,[0.1 200.0],'fft_BPF');
% 3次バターワースによるLPF(200Hz)の例
% filtered = filtering(data,1000.0,[200.0 3],'butter_LPF');
% 5次バターワースによるHPF(0.1Hz)の例
% filtered = filtering(data,1000.0,[0.1 5],'butter_HPF');
% 2次バターワースによるBPF(0.1Hz-200Hz)の例
% filtered = filtering(data,1000.0,[0.1 200.0 2],'butter_BPF');
%

if nargin==2
    type = 'fft_LPF';
end

if strcmp(type,'fft_LPF')
    data = [data;data(end:-1:1,:)];
    cutoff = param;
    freq = data_freq*(0:floor(size(data,1)/2))/size(data,1);
    if (mod(size(data,1),2)==0)
        freq = [freq freq((end-1):-1:2)];
    else
        freq = [freq freq(end:-1:2)];
    end
    idx = find(freq'>cutoff);
    filtered = fft(data);
    filtered(idx,:) = zeros(length(idx),size(filtered,2));
    filtered = real(ifft(filtered));
    filtered = filtered(1:end/2,:);
elseif strcmp(type,'fft_HPF')
    data = [data;data(end:-1:1,:)];
    cutoff = param;
    freq = data_freq*(0:floor(size(data,1)/2))/size(data,1);
    if (mod(size(data,1),2)==0)
        freq = [freq freq((end-1):-1:2)];
    else
        freq = [freq freq(end:-1:2)];
    end
    idx = find(freq'<cutoff);
    filtered = fft(data);
    filtered(idx,:) = zeros(length(idx),size(filtered,2));
    filtered = real(ifft(filtered));
    filtered = filtered(1:end/2,:);
elseif strcmp(type,'fft_BPF')
    data = [data;data(end:-1:1,:)];
    freq = data_freq*(0:floor(size(data,1)/2))/size(data,1);
    if (mod(size(data,1),2)==0)
        freq = [freq freq((end-1):-1:2)];
    else
        freq = [freq freq(end:-1:2)];
    end
    idx = find(freq'<param(1)|freq'>param(2));
    filtered = fft(data);
    filtered(idx,:) = zeros(length(idx),size(filtered,2));
    filtered = real(ifft(filtered));
    filtered = filtered(1:end/2,:);
elseif strcmp(type, 'butter_LPF')
    [b,a] = butter(param(2),param(1)/data_freq*2);
    filtered = filter(b,a,data);
elseif strcmp(type, 'butter_HPF')
    [b,a] = butter(param(2),param(1)/data_freq*2,'high');
    filtered = filter(b,a,data);
elseif strcmp(type, 'butter_BPF')
    [b,a] = b(param(3),[param(1) param(2)]/data_freq*2);
    filtered = filter(b,a,data);
end

