 **1.1. 项目目标**

需要实现支持多用户的智能对话代理，帮助用户通过聊天界面管理餐厅预订。是一个必须在两天之内完成的编程任务，绝对不是一个复杂的分布式系统。禁止任何的过度工程，

**2. 核心功能需求**
  **查询**：询问餐厅的可用性和政策。
  **创建**：进行新的预订。
  **检查**：查看已有的预订详情。
  **修改/取消**：更改或取消已有的预订。
  **状态管理**：必须在多轮对话中维持会话状态。

**API 集成要求**
  **连接**：必须与提供的模拟预订服务器 (`http://localhost:8547`) 进行交互。
  **端点**：使用其已有的API端点完成所有操作。
  **认证**：正确处理`Bearer`令牌认证。
  **数据格式**：请求的`Content-Type`需为`application/x-www-form-urlencoded`。
  **错误处理**：优雅地处理API错误和无效请求。
  **参数校验**：在调用API前，确保预订参数的有效性。

=========================
## 模拟预订服务器的api文档如下：
# Authentication

All endpoints require a Bearer token in the Authorization header.

**Required Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8
```

**Authentication Errors:**
- **401 Unauthorised**: Missing, invalid, or expired token
- **401 Unauthorised**: Invalid authorisation header format

## API Endpoints

All endpoints use `application/x-www-form-urlencoded` content type for POST/PATCH requests and require the Authorization header.

### 1. Search Available Time Slots
**POST** `/api/ConsumerApi/v1/Restaurant/{restaurant_name}/AvailabilitySearch`

Returns available booking slots for a specific date and party size.

**Parameters:**
- `VisitDate`: Date in YYYY-MM-DD format (required)
- `PartySize`: Number of people (required)
- `ChannelCode`: Booking channel, typically "ONLINE" (required)

**Response:**
```json
{
  "restaurant": "TheHungryUnicorn",
  "restaurant_id": 1,
  "visit_date": "2025-08-06",
  "party_size": 2,
  "channel_code": "ONLINE",
  "available_slots": [
    {
      "time": "12:00:00",
      "available": true,
      "max_party_size": 8,
      "current_bookings": 0
    }
  ],
  "total_slots": 8
}
```

### 2. Create New Booking
**POST** `/api/ConsumerApi/v1/Restaurant/{restaurant_name}/BookingWithStripeToken`

Creates a new restaurant booking with customer information.

**Required Parameters:**
- `VisitDate`: Date in YYYY-MM-DD format
- `VisitTime`: Time in HH:MM:SS format
- `PartySize`: Number of people
- `ChannelCode`: Booking channel (e.g., "ONLINE")

**Optional Parameters:**
- `SpecialRequests`: Special requirements text
- `IsLeaveTimeConfirmed`: Boolean for time confirmation
- `RoomNumber`: Specific room/table number

**Customer Information (all optional):**
- `Customer[Title]`: Mr/Mrs/Ms/Dr
- `Customer[FirstName]`: Customer's first name
- `Customer[Surname]`: Customer's last name
- `Customer[Email]`: Email address
- `Customer[Mobile]`: Mobile phone number
- `Customer[Phone]`: Landline phone number
- `Customer[MobileCountryCode]`: Mobile country code
- `Customer[PhoneCountryCode]`: Phone country code
- `Customer[ReceiveEmailMarketing]`: Boolean for email marketing consent
- `Customer[ReceiveSmsMarketing]`: Boolean for SMS marketing consent

**Response:**
```json
{
  "booking_reference": "ABC1234",
  "booking_id": 1,
  "restaurant": "TheHungryUnicorn",
  "visit_date": "2025-08-06",
  "visit_time": "12:30:00",
  "party_size": 4,
  "status": "confirmed",
  "customer": {
    "id": 1,
    "first_name": "John",
    "surname": "Smith",
    "email": "john@example.com"
  },
  "created_at": "2025-08-06T10:30:00.123456"
}
```

### 3. Get Booking Details
**GET** `/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}`

Retrieves complete booking information.

**Response:**
```json
{
  "booking_reference": "ABC1234",
  "booking_id": 1,
  "restaurant": "TheHungryUnicorn",
  "visit_date": "2025-08-06",
  "visit_time": "12:30:00",
  "party_size": 4,
  "status": "confirmed",
  "special_requests": "Window table please",
  "customer": {
    "id": 1,
    "first_name": "John",
    "surname": "Smith",
    "email": "john@example.com",
    "mobile": "1234567890"
  },
  "created_at": "2025-08-06T10:30:00.123456",
  "updated_at": "2025-08-06T10:30:00.123456"
}
```

### 4. Update Booking
**PATCH** `/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}`

Modifies an existing booking. Only provide fields you want to change.

**Optional Parameters:**
- `VisitDate`: New date (YYYY-MM-DD)
- `VisitTime`: New time (HH:MM:SS)
- `PartySize`: New party size
- `SpecialRequests`: Updated special requests
- `IsLeaveTimeConfirmed`: Time confirmation status

**Response:**
```json
{
  "booking_reference": "ABC1234",
  "booking_id": 1,
  "restaurant": "TheHungryUnicorn",
  "updates": {
    "party_size": 6,
    "special_requests": "Updated request"
  },
  "status": "updated",
  "updated_at": "2025-08-06T11:30:00.123456",
  "message": "Booking ABC1234 has been successfully updated"
}
```

### 5. Cancel Booking
**POST** `/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}/Cancel`

Cancels an existing booking with a reason.

**Parameters:**
- `micrositeName`: Restaurant microsite name (same as restaurant_name)
- `bookingReference`: Booking reference (same as in URL)
- `cancellationReasonId`: Reason ID (1-5, see cancellation reasons below)

**Response:**
```json
{
  "booking_reference": "ABC1234",
  "booking_id": 1,
  "restaurant": "TheHungryUnicorn",
  "cancellation_reason_id": 1,
  "cancellation_reason": "Customer Request",
  "status": "cancelled",
  "cancelled_at": "2025-08-06T12:30:00.123456",
  "message": "Booking ABC1234 has been successfully cancelled"
}
```

## Cancellation Reasons

| ID | Reason | Description |
|----|--------|-------------|
| 1 | Customer Request | Customer requested cancellation |
| 2 | Restaurant Closure | Restaurant temporarily closed |
| 3 | Weather | Cancelled due to weather conditions |
| 4 | Emergency | Emergency cancellation |
| 5 | No Show | Customer did not show up |

## Error Responses

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful operation
- **400 Bad Request**: Invalid parameters or business rule violation
- **404 Not Found**: Restaurant or booking not found
- **422 Unprocessable Entity**: Validation errors

Error response format:
```json
{
  "detail": "Error description"
}
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8547/docs
- Alternative docs: http://localhost:8547/redoc

## Example Requests

### 1. Check Availability
```bash
curl -X POST "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn/AvailabilitySearch" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "VisitDate=2025-08-06&PartySize=2&ChannelCode=ONLINE"
```

### 2. Make a Booking
```bash
curl -X POST "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn/BookingWithStripeToken" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "VisitDate=2025-08-06&VisitTime=12:30:00&PartySize=4&ChannelCode=ONLINE&SpecialRequests=Window table please&Customer[FirstName]=John&Customer[Surname]=Smith&Customer[Email]=john@example.com&Customer[Mobile]=1234567890"
```

### 3. Get Booking Details
```bash
curl -X GET "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn/Booking/ABC1234" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8"
```

### 4. Update Booking
```bash
curl -X PATCH "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn/Booking/ABC1234" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "PartySize=6&SpecialRequests=Updated request"
```

### 5. Cancel Booking
```bash
curl -X POST "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn/Booking/ABC1234/Cancel" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "micrositeName=TheHungryUnicorn&bookingReference=ABC1234&cancellationReasonId=1"
```
==================================

## 本项目设计

1.  **状态机驱动 (State-Machine Driven)**: 整个对话流程将由一个显式的、确定性的状态机（使用LangGraph框架实现）来精确管理。这意味着每一次状态转换都有明确的条件和可预测的结果，使得复杂的对话工作流变得可观察、可调试、可信赖。

2.  **结构化交互 (Structured Interaction)**: “菜单与表单填充”模型。系统在交互中占据主导地位，通过清晰的菜单选项确定用户意图，再通过引导式的表单填充流程收集必要信息。这种模式极大地降低了用户的认知负荷，避免了因开放式对话带来的模糊性和不确定性，从而显著提高任务成功率。

3.  **闭环错误处理 (Closed-Loop Error Handling)**: “检测 -> 隔离 -> 引导式恢复”模型。
      **检测与隔离**发生在Python工具层，通过Pydantic的严格验证捕获所有无效或不完整的用户输入。
      **引导式恢复**发生在Agent（LLM）层，Agent接收来自工具层的精确错误反馈，并生成高度针对性的、人性化的问题来引导用户纠正错误，从而形成一个完整的、自动化的错误处理闭环。

4.  **持久化与个性化 (Persistence & Personalization)**: 系统必须能够服务多个用户，并记住他们。通过引入数据库层，我们实现了：
      **用户认证与隔离**: 确保每个用户的数据（个人资料、聊天记录）都是安全隔离的。
      **状态持久化**: 即使用户关闭会话后重新登录，其对话历史和个人偏好依然存在。
      **个性化服务**: Agent能够主动利用存储在数据库中的用户个人资料（如姓名、邮箱、联系电话）作为默认值，从而简化交互流程，提供“懂你”的体验。

5.  **高度内聚、低度耦合的关注点分离 (Separation of Concerns)**: 系统的每个模块都有单一、明确的职责，模块之间通过定义良好的接口进行通信。这使得系统易于理解、修改和测试。
      **UI层**: 纯粹的表示层。
      **API服务层 (FastAPI)**: 负责HTTP协议、用户会话管理和作为系统各部分的协调者。
      **数据库层**: 负责所有数据的持久化存储和检索。
      **Agent核心 (LangGraph)**: 负责对话流的逻辑编排。
      **工具层**: 负责执行原子任务和输入验证。
      **API客户端层**: 负责与外部服务进行底层通信。

### **2. 系统架构**

#### **2.1. 宏观架构图**

```mermaid
graph TD
    subgraph 用户端
        A[用户 (通过命令行或Web界面)]
    end

    subgraph 应用服务器 (Python)
        B[表示层/UI (main.py)]
        C[API服务层 (FastAPI Endpoints)]
        H[数据库层 (SQLAlchemy + CRUD)]
        D[Agent核心 (LangGraph 状态机)]
        E[工具层 (原子工具 + Pydantic验证)]
        F[API客户端层 (Requests封装)]
    end

    subgraph 外部服务
        G[模拟预订API服务器 (all.txt)]
    end

    A -- 用户输入 --> B
    B -- 构造请求 --> C
    C -- 读/写用户数据 --> H
    C -- 构建初始AgentState --> D
    D -- 决策/编排 --> E
    E -- 使用 --> F
    F -- HTTP请求 --> G
    G -- HTTP响应 --> F
    F -- 返回结构化数据 --> E
    E -- 返回观察结果 --> D
    D -- 更新状态/生成回复 --> C
    C -- 返回最终响应 --> B
    B -- 呈现给用户 --> A
```

#### **2.2. 项目文件结构**

一个清晰、逻辑化的文件结构是高效开发和长期维护的基石。

```
restaurant-booking-agent/
├── .env                  # 存储所有环境变量，如API密钥和数据库连接字符串
├── main.py               # 应用主入口：启动FastAPI服务，定义API端点，集成命令行UI
├── requirements.txt      # 项目的所有Python依赖库
│
└── src/
    ├── __init__.py
    │
    ├── agent/
    │   ├── __init__.py
    │   ├── state.py      # 定义核心的AgentState数据结构，作为状态机的工作内存
    │   ├── graph.py      # LangGraph状态机的构建：定义所有节点和条件边，编排核心工作流
    │   └── prompts.py    # 集中管理所有与LLM交互的Prompt模板
    │
    ├── api/
    │   ├── __init__.py
    │   ├── client.py     # 封装对外部模拟API服务器的所有HTTP请求，处理认证和数据格式
    │   └── schemas.py    # 定义与外部API数据结构严格对应的Pydantic模型
    │
    ├── database/
    │   ├── __init__.py
    │   ├── models.py     # 定义数据库的表结构 (SQLAlchemy ORM模型)
    │   ├── crud.py       # 封装所有数据库的增删改查(CRUD)操作
    │   └── session.py    # 数据库会话管理
    │
    ├── tools/
    │   ├── __init__.py
    │   ├── definitions.py # 定义所有供Agent使用的原子工具函数 (@tool)
    │   └── schemas.py     # 为每个工具的输入参数定义严格的Pydantic验证模型
    │
    └── config.py             # 加载和管理.env中的配置，提供类型安全的全局配置对象
```

### **3. 核心工作流设计**

我们将使用状态图来可视化定义每个核心功能的工作流。这些图将直接映射到`src/agent/graph.py`中的LangGraph实现。

#### **3.1. 主工作流：意图路由**

这是所有交互的入口。

```mermaid
stateDiagram-v2
    [*] --> AwaitingInput
    AwaitingInput --> RouteIntent: 用户输入
    RouteIntent --> CheckAvailabilityFlow: 意图: 查可用性
    RouteIntent --> CreateBookingFlow: 意图: 新建预订
    RouteIntent --> GetBookingFlow: 意图: 查预订
    RouteIntent --> ModifyBookingFlow: 意图: 修改预订
    RouteIntent --> CancelBookingFlow: 意图: 取消预订
    RouteIntent --> HandleUnknown: 意图: 未知
    HandleUnknown --> AwaitingInput: 提示用户重新选择
```

#### **3.2. 子工作流：创建预订 (CreateBookingFlow)**

表单填充、前置条件检查和闭环错误处理。

```mermaid
stateDiagram-v2
    state "表单填充循环" as FormLoop {
        FillForm: 开始填充表单
        FillForm --> FillForm: 自动填充(使用Profile)
        FillForm --> AskUser: 需要用户输入
        AskUser --> FillForm: 用户回答
        state "验证失败？" as Validate
        FillForm --> Validate: 字段无效
        Validate --> AskUser: **引导式恢复**
    }
    
    [*] --> FormLoop
    FormLoop --> PreBookingCheck: 表单完成
    PreBookingCheck: **调用check_availability工具**
    PreBookingCheck --> ExecuteBooking: **时段可用**
    PreBookingCheck --> FormLoop: **时段不可用 (重置时间字段并引导)**
    ExecuteBooking: 调用create_booking工具
    ExecuteBooking --> FormatResponse: 预订成功
    ExecuteBooking --> FormLoop: **预订失败 (参数错误)**
    FormatResponse --> [*]
```

### **4. 模块详细设计**

#### **4.1. 数据库层 (`src/database/`)**

  **`models.py`**:
      **`User` 模型**:
          `id` (Integer, PK), `username` (String, Unique), `hashed_password` (String)。
          `profile_json` (Text, non-nullable, default=`'{}'`)：**核心个性化字段**。它将存储一个JSON字符串，其结构可以灵活扩展，例如：
            ```json
            {
              "Customer[Title]": "Mr",
              "Customer[FirstName]": "John",
              "Customer[Surname]": "Doe",
              "Customer[Email]": "john.doe@example.com",
              "Customer[Mobile]": "1234567890",
              "Customer[ReceiveEmailMarketing]": true,
              "Customer[ReceiveSmsMarketing]": false
            }
            ```
            我们直接使用后端API期望的`Customer[...]`格式作为键，这简化了后续的数据准备工作。
      **`ChatSession` 模型**:
          `id` (Integer, PK), `session_id` (String, Unique), `user_id` (FK to User), `history_json` (Text), `created_at`, `updated_at`。

  **`crud.py`**:
      提供高级、业务逻辑无关的数据库操作函数。所有函数都接收一个`db: Session`参数。
      `get_user_by_username(db, username)`: 通过用户名查找用户。
      `create_user(db, username, password, profile_dict)`: 创建新用户。内部处理密码哈希（使用`passlib`）和`profile_dict`到JSON字符串的序列化。
      `update_user_profile(db, user_id, new_profile_dict)`: 更新用户个人资料。
      `verify_user(db, username, password)`: 验证用户名和密码，成功则返回User对象。
      `create_or_get_session(db, user_id)`: 为用户创建或获取一个有效的会话，返回`ChatSession`对象。
      `update_chat_history(db, session_id, history_list)`: 将`history_list`序列化为JSON并更新到数据库。

#### **4.2. 工具层 (`src/tools/`)**

  **`schemas.py`**:
      为每个工具的输入参数定义Pydantic模型，包含丰富的验证规则。
      **`CreateBookingArgs(BaseModel)`**:
          `visit_date: date`
          `visit_time: time`
          `party_size: int = Field(gt=0, description="Party size must be a positive integer.")`
          `first_name: str = Field(min_length=1, description="First name cannot be empty.")`
          `surname: str = Field(min_length=1, description="Surname cannot be empty.")`
          `email: EmailStr` (使用Pydantic内置的Email格式验证)

  **`definitions.py`**:
      定义所有`@tool`函数。每个函数都是**原子化、无状态且健壮的**。
      **`create_booking` 工具实现模板**:
        ```python
        @tool
        def create_booking(visit_date: str, visit_time: str, party_size: int, first_name: str, surname: str, email: str) -> str:
            """Creates a new booking with the provided details. All parameters are required."""
            try:
                # 1. 检测与隔离：使用Pydantic模型进行严格校验
                args = tool_schemas.CreateBookingArgs(
                    visit_date=visit_date, visit_time=visit_time, party_size=party_size,
                    first_name=first_name, surname=surname, email=email
                )
            except ValidationError as e:
                # 2. 返回精确的、可操作的错误信息
                err = e.errors()[0]
                field, msg = err['loc'][0], err['msg']
                return f"Parameter Error: The field '{field}' is invalid. Reason: {msg}. Please ask the user for a correction."

            # 3. 如果验证成功，调用API客户端
            try:
                # 构造API客户端需要的请求模型
                customer_info = api_schemas.CustomerInfo(FirstName=args.first_name, Surname=args.surname, Email=args.email)
                req = api_schemas.BookingRequest(
                    VisitDate=args.visit_date, VisitTime=args.visit_time, PartySize=args.party_size,
                    Customer=customer_info, ChannelCode="ONLINE"
                )
                response = api_client.create_booking(req)
                # 4. 返回结构化的成功结果
                return response.model_dump_json()
            except Exception as e:
                # 捕获API调用层的错误
                return json.dumps({"error": f"API call failed during booking creation: {e}"})
        ```

#### **4.3. Agent核心 (`src/agent/`)**

  **`state.py`**:
      定义`AgentState(TypedDict)`，作为整个状态机的工作内存。
      **完整字段**:
          `user_id: int`: 当前用户的ID。
          `user_profile: dict`: 从数据库加载的、包含用户默认信息的字典。
          `input: str`: 用户最新的原始输入。
          `chat_history: list[BaseMessage]`: 完整的对话历史。
          `intent: Intent`: 由路由节点确定的用户意图。
          `form_data: dict`: 在表单填充循环中，已成功收集并验证的字段和值。
          `required_fields: list[str]`: 当前意图所需的所有字段名列表。
          `validation_error: Optional[str]`: 从工具层返回的精确验证错误，用于驱动引导式恢复。
          `tool_output: Optional[str]`: 最新工具调用的原始JSON输出。
          `final_response: Optional[str]`: 准备返回给用户的最终自然语言回复。

  **`prompts.py`**:
      **`ROUTER_PROMPT`**: "根据用户的最新输入 `{input}`，从以下选项中选择最匹配的用户意图：`['check_availability', 'create_booking', ...]`。仅返回意图的字符串。"
      **`FORM_FILLING_PROMPT`**: 这是最复杂的Prompt，它驱动着信息收集和错误恢复。
          **输入**: `user_input`, `user_profile`, `required_fields`, `form_data`, `validation_error`。
          **核心指令**:
            1.  "你的任务是填充一个表单。必需字段是 `{required_fields}`。已填充字段是 `{form_data}`。"
            2.  "**如果 `{validation_error}` 存在**，这意味着用户上次的输入是无效的。请根据错误信息 `{validation_error}`，生成一个清晰、友好的问题来引导用户修正这个特定的错误。"
            3.  "**如果 `{validation_error}` 不存在**，按以下顺序操作："
            4.  "首先，检查 `{required_fields}` 中还有哪些字段未在 `{form_data}` 中。对于第一个未填充的字段，检查用户的个人资料 `{user_profile}` 中是否有对应的值。如果有，自动用它填充 `{form_data}`，然后重复此步骤检查下一个未填充字段。"
            5.  "当自动填充结束后，如果表单仍未完整，请针对第一个尚未填充的字段，向用户提出一个明确的问题。"
            6.  "分析用户的最新输入 `{user_input}`，尝试从中提取信息来填充表单。"
            7.  "你的最终输出必须是一个JSON对象，包含两个键：`question` (如果需要继续提问，则为问题字符串；否则为`null`) 和 `updated_form_data` (更新后的表单字典)。"
      **`RESPONSE_FORMATTER_PROMPT`**: "用户的请求是 `{input}`。一个工具成功执行并返回了以下JSON数据：`{tool_output}`。请将这个技术性的JSON数据转换成一句友好、简洁、自然的中文回复给用户。"

  **`graph.py`**:
      使用LangGraph构建状态机。
      **节点 (Nodes)**:
          `route_intent_node`: 调用`ROUTER_PROMPT`，更新`state.intent`和`state.required_fields`。
          `form_filling_node`: 调用`FORM_FILLING_PROMPT`，处理表单逻辑。
          `tool_execution_node`: 根据`state.intent`和`state.form_data`，选择并调用相应的原子工具。
          `response_formatter_node`: 调用`RESPONSE_FORMATTER_PROMPT`，生成最终回复。
      **条件边 (Conditional Edges)**:
          `after_routing`: 从`route_intent_node`出发，直接进入`form_filling_node`。
          `after_form_filling`:
              **IF** `question` is not `null` in the LLM output, **THEN** 循环回到`form_filling_node`的入口（实际上是结束图的执行，将问题返回给用户，下一次用户输入将再次进入此节点）。
              **IF** `question` is `null` (表单完成) **AND** `intent == 'create_booking'`, **THEN** 触发一个特殊的`pre_check`标志，并进入`tool_execution_node`（执行`check_availability`）。
              **IF** `question` is `null` **AND** `intent != 'create_booking'`, **THEN** 直接进入`tool_execution_node`。
          `after_tool_execution`:
              **IF** `tool_output` 包含 `"Parameter Error"`, **THEN** 将错误信息存入`state.validation_error`，并**返回**到`form_filling_node`进行引导式恢复。
              **IF** `tool_output` 显示预订前检查不可用, **THEN** 将“时段不可用”信息存入`state.validation_error`，清空`form_data`中的时间日期，并**返回**到`form_filling_node`。
              **IF** `tool_output` 是成功的JSON, **THEN** 进入`response_formatter_node`。
              **IF** `tool_output` 包含API错误, **THEN** 直接进入`response_formatter_node`以报告API错误。
          `after_formatting`: 边指向`END`，图执行结束。

#### **4.4. 主应用与UI层 (`main.py`)**

  **职责**:
    1.  **启动**: 初始化数据库连接，编译LangGraph应用。
    2.  **定义FastAPI端点**:
          `/register`, `/login`: 处理用户认证，返回`session_id`。
          `/profile`: 提供`GET`和`PUT`方法，允许用户查看和更新自己的个人资料。
          `/chat`: 核心交互端点，严格按照3.2.A节描述的逻辑实现：加载会话 -> 构建初始状态 -> 调用Agent -> 持久化结果 -> 返回响应。
    3.  **（可选）命令行界面**:
          提供一个简单的命令行版本，用于开发和调试。
          启动时要求用户“登录”或“注册”。
          登录后，将`session_id`保存在一个变量中，并在每次与Agent交互时使用它。

### **5. 完整端到端工作流示例：Profile感知的预订**

此示例展示了所有组件如何协同工作，为已登录用户提供无缝体验。

1.  **用户登录**: 用户"JohnDoe"通过`/login`端点登录，客户端收到并存储`session_id`。
2.  **用户发起预订**: 客户端发送请求到`POST /chat`，请求体为`{"session_id": "...", "message": "帮我订一张明晚7点的两人桌"}`。
3.  **FastAPI后端**:
      使用`session_id`从数据库加载JohnDoe的`user_profile`和`chat_history`。
      构建`initial_state`，其中`user_profile`字段包含了John的完整个人资料。
      调用`agent_app.invoke(initial_state)`。
4.  **LangGraph执行**:
      **`route_intent_node`**: 确定意图为`create_booking`。
      **`form_filling_node`**:
          LLM解析用户输入，填充`visit_date`, `visit_time`, `party_size`。
          LLM根据Prompt指令，检查`user_profile`，自动填充`first_name`, `surname`, `email`。
          表单瞬间完成，无需向用户提问。
      **`conditional_after_form_filling`**: 检测到表单完成，意图为`create_booking`，进入`tool_execution_node`执行`check_availability`。
      **`tool_execution_node` (第一次)**:
          调用`check_availability`工具。假设时段可用，返回成功的JSON。
      **`conditional_after_tool_execution`**: 检测到预订前检查成功，再次进入`tool_execution_node`。
      **`tool_execution_node` (第二次)**:
          调用`create_booking`工具，传入所有已填充的参数。
          工具内部Pydantic验证通过。
          API客户端被调用，预订成功，返回包含预订参考号的JSON。
      **`conditional_after_tool_execution`**: 检测到工具成功执行，进入`response_formatter_node`。
      **`response_formatter_node`**: LLM将预订成功的JSON转换为“好的，John！您在TheHungryUnicorn的预订已确认，时间是明天晚上7点，两人桌。您的预订参考号是XYZ123。”
5.  **FastAPI后端**:
      从`final_state`中获取最终回复和更新后的`chat_history`。
      将`chat_history`写回数据库。
      将最终回复返回给客户端。
6.  **UI**: 显示Agent的确认信息。

