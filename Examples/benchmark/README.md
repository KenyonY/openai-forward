

## 原始benchmark接口测试
> http://localhost:8080  
> 该部分测试是为评估`fastapi`本身流式与非流式返回的性能,不涉及转发

启动参数: `BENCHMARK_MODE=true aifd run --workers=n --port 8080` (n=1 or 4)



### stream == false:
```bash
wrk -t8 -c400 -d10s -s post.lua http://localhost:8080/benchmark/v1/chat/completions
```
单核:

![img_7.png](img_7.png)


4核:

![img_8.png](img_8.png)


### stream == true:
```bash
wrk -t8 -c100 -d10s -s post.lua http://localhost:8080/benchmark/v1/chat/completions
```
从下面的测试中可以发现，对于fastapi的流式返回时的Request/sec并不高，这里其实还应该添加不同流式返回时间的测试,
目前流式返回的文本在`cache/chat`中, 下面的结果中没有设置`TOKEN_RATE_LIMIT`，可以添加不同的`TOKEN_RATE_LIMIT`进行测试以模拟实际情况。

单核:

![img_10.png](img_10.png)

4核:

![img.png](img.png)

## 转发benchmark接口
> http://localhost:8000  
> 该部分评估流式与非流式转发的性能


启动参数: `OPENAI_BASE_URL=http://localhost:8080 aifd run --workers=n --port 8000` (n=1 or 4)
```bash
wrk -t8 -c100 -d10s -s post.lua http://localhost:8000/benchmark/v1/chat/completions
```

### stream == false:

**单核**

![img_5.png](img_5.png)

**4核**:(原始与转发两边均4核)  

![img_2.png](img_2.png)

### stream == true:

**单核**: (是的，转发时的结果比原始的还要好,比较迷~)

![img_4.png](img_4.png)

**4核**:(原始与转发两边均4核)

![img_3.png](img_3.png)



