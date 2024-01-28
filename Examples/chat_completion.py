from openai import OpenAI
from rich import print
from sparrow import MeasureTime, yaml_load  # pip install sparrow-python

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")

client = OpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)

stream = True

n = 1

debug = False

max_tokens = None

# user_content = """
# 用c实现目前已知最快平方根算法
# """
# user_content = '最初有1000千克的蘑菇，其中99%的成分是水。经过几天的晴天晾晒后，蘑菇中的水分含量现在是98%，蘑菇中减少了多少水分？'
# user_content = "Write down the most romantic sentence you can think of."
user_content = "光散射中的Mie理论的理论公式是怎样的？请用latex语法表示它公式使用$$符号包裹。"

model = "gpt-3.5-turbo"
# model="gpt-4"

mt = MeasureTime().start()

resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": user_content},
    ],
    stream=stream,
    n=n,
    max_tokens=max_tokens,
    timeout=30,
    # extra_body={"caching": True},
)

if stream:
    if debug:
        for chunk in resp:
            print(chunk)
    else:
        for idx, chunk in enumerate(resp):
            chunk_message = chunk.choices[0].delta or ""
            if idx == 0:
                mt.show_interval("tcp time:")
                print(f"{chunk_message.role}: ")
                continue
            content = chunk_message.content or ""
            print(content, end="")
        print()
else:
    print(resp)
    assistant_content = resp.choices[0].message.content
    print(assistant_content)
    print(resp.usage)

mt.show_interval("chat")
"""
gpt-4:

以下是用C语言实现的最快已知的一种平方根算法，也叫做 "Fast Inverse Square Root"。这种算法首次出现在雷神之锤3的源代码中，被大量的现代3D图形计算所使用。

```c
#include <stdint.h>

float Q_rsqrt(float number){
    long i;
    float x2, y;
    const float threehalfs = 1.5F;

    x2 = number * 0.5F;
    y  = number;
    i  = * ( long * ) &y;
    i  = 0x5f3759df - ( i >> 1 );
    y  = * ( float * ) &i;
    y  = y * ( threehalfs - ( x2 * y * y ) );

    return y;
}
```
这种算法的精确度并不是很高，但它的速度快到足以做实时图形计算。上述代码的主要思想是通过对IEEE 754浮点数表示法的理解和利用，借助整数和浮点数的二进制表示在略有不同的特性，实现了快速逼近求解平方根倒数的方法。

注意，这个函数实际上求解的是平方根的倒数，也就是1/sqrt(x)，如果需要得到sqrt(x)的结果，只需要将函数返回值取倒数即可。这是因为在3D图形计算中，往往更频繁地需要求解平方根倒数，而直接求解平方根反而较为罕见。


----------------------------------------------------------------------------------------------------------------------------------------------------------------

gpt-3.5-turbo:

目前已经发现的最快平方根算法是牛顿迭代法，可以用C语言实现如下：

```c
#include <stdio.h>

double sqrt_newton(double x) {
    if (x == 0) {
        return 0;
    }
    
    double guess = x / 2;  // 初始猜测值为x的一半
    
    while (1) {
        double new_guess = (guess + x / guess) / 2;  // 根据牛顿迭代法计算新的猜测值
        if (new_guess == guess) {  // 如果新的猜测值与上一次的猜测值相同，迭代结束
            break;
        }
        guess = new_guess;
    }
    
    return guess;
}

int main() {
    double x = 16;  // 以16为例进行测试
    double result = sqrt_newton(x);
    printf("The square root of %lf is %lf\n", x, result);
    
    return 0;
}
```

该程序使用牛顿迭代法来计算平方根，初始猜测值为待开方数的一半。然后通过迭代计算新的猜测值，直到新的猜测值与上一次的猜测值相同，迭代结束。最后输出计算得到的平方根结果。


"""
