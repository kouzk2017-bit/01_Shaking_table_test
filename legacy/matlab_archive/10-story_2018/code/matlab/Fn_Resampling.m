function [x,deltaT] = Fn_Resampling(x_,old_dt,new_dt)

[N,D] = rat(old_dt/new_dt,1e-6);

if N==D
  x=x_;
  deltaT = old_dt;
  return;
end

deltaT = old_dt*D/N;
x = x_([1:end,end:-1:1],:);
x = fft(x);
x = [x(1:((end-mod(end,2))/2+1),:);...
    zeros(size(x,1)*(N-1),size(x,2));...
    x(((end-mod(end,2))/2+2):end,:)];


if D>N
    freq = (0:fix(size(x,1)/2))/size(x,1)/old_dt*N;
    freq = [freq freq((end-1+mod(size(x,1),2)):-1:2)];
    idx = find(freq>0.5/deltaT);
    x(idx,:) = zeros(length(idx),size(x,2));
end

x = real(ifft(x)*N);

x = x(1:D:end/2,:);

