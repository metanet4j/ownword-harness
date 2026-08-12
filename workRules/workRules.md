BDD 是 **Behavior-Driven Development，行为驱动开发**。

它是在 TDD（测试驱动开发）基础上发展出来的一种开发方式，重点不是“这个方法怎么测试”，而是：

> **站在用户/业务行为的角度，描述系统应该做什么。**

你看到的 **Given / When / Then** 就是 BDD 最典型的表达形式：

- **Given**：给定什么前置条件
- **When**：发生什么操作/事件
- **Then**：应该得到什么结果

例如登录场景：

```
Given 用户已经注册，用户名和密码正确
When 用户提交登录请求
Then 登录成功，并返回访问令牌
```

如果对应 Java 测试，可以理解成：

```
@Test
void should_login_successfully_when_credentials_are_correct() {
    // Given
    String username = "test";
    String password = "123456";

    // When
    LoginResult result = loginService.login(username, password);

    // Then
    assertTrue(result.isSuccess());
    assertNotNull(result.getToken());
}
```

### BDD 和 TDD 的区别

可以简单理解为：

|                | TDD                     | BDD                         |
| -------------- | ----------------------- | --------------------------- |
| 全称           | Test-Driven Development | Behavior-Driven Development |
| 中文           | 测试驱动开发            | 行为驱动开发                |
| 关注点         | 代码是否正确            | 系统行为是否符合业务预期    |
| 常见表达       | Arrange / Act / Assert  | Given / When / Then         |
| 更适合沟通对象 | 开发人员                | 产品、测试、开发共同理解    |

实际上两者并不冲突。

例如你做 Spring Boot 项目时，我比较推荐：

```
业务需求
    ↓
BDD：Given / When / Then 描述行为
    ↓
TDD：先写失败测试
    ↓
实现代码
    ↓
测试通过
    ↓
重构
```

比如订单取消：

```
Given
订单状态为 PAID

When
用户取消订单

Then
订单状态变成 CANCELLED
并触发退款
```

这种写法最大的价值是：**测试本身就是业务规则的可执行文档。**

所以你以后看到：

```
// given
...

// when
...

// then
...
```

本质上就是开发者把一个测试拆成：

**前置条件 → 行为 → 预期结果**

这也是 Java/Spring Boot 单元测试里非常推荐的一种结构。