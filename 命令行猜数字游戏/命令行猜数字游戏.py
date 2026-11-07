# 猜数字游戏 命令行版


# while循环（计算1-100累加、偶数和）
sum = 0
i = 1
while i <= 100:
    sum += i
    i += 1
print(f"1~100的累加结果为：{sum}")

sum = 0
i = 2
while i <= 100:
    sum += i
    i += 2
print(f"1~100的偶数和结果为：{sum}")

sum = 0
i = 1
while i <= 100:
    sum += i
    i += 2
print(f"1~100的奇数和结果为：{sum}")


# while循环打印九九乘法表
i = 1
j = 1
while i <= 9:
    while j <= i:
        print(f"{j}*{i}={j*i}", end = " ")
        j += 1
    j = 1
    i += 1
    print("")


# for循环打印九九乘法表
for i in range(1,10):
    for j in range(1,i+1):
        print(f"{j}*{i}={j*i}", end = " ")
    print("")


# 嵌套循环打印直角三角形
for i in range(1,5):
    for j in range(1,i+1):
        print("*", end="  ")
    print("")


# 命令行猜数字游戏（完整版）
import random

num = random.randint(1,100)
count = 1

while count <= 7:
    guess_num = input("请输入一个猜测的数字：")

    if guess_num == "quit":
        print("用户退出游戏！")
        break

    guess_num = int(guess_num)
    
    if guess_num == num:
        print(f"恭喜你用了{count}次猜对！")
        break
    elif guess_num > num:
        print("猜大了！")
    else:
        print("猜小了！")
        
    count += 1

if count == 8:
    print(f"最多猜7次，游戏失败！数字为{num}")
