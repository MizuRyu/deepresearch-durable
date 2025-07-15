from loguru import logger

from function_app import app

from ..core.prompts import SUMMARIZER_INSTRUCTIONS
from ..core.llms import call_aoai

@app.function_name(name="contentSummarize_activity")
@app.activity_trigger(input_name="input")
async def contentSummarize_activity(input: dict):
    logger.info(f"[contentSummarize_activity] Start Activity")

    topic = input.get("topic", "")
    existing_summary = input.get("existing_summary", "")
    recent_web_research_result = input.get("recent_web_research_result", "")

    if existing_summary:
        human_message_content = (
            f"<Existing Summary> \n {existing_summary} \n </Existing Summary>\n\n"
            f"<New Context> \n {recent_web_research_result} \n </New Context>"
            f"このトピックの新しいContextで既存のSummaryを更新: \n <User Input> \n {topic} \n </User Input>\n\n"
        )
    else:
        human_message_content = (
            f"<Context> \n {recent_web_research_result} \n </Context>"
            f"このトピックののContextを使用してSummaryを作成: \n <User Input> \n {topic} \n </User Input>\n\n"
        )

    response = await call_aoai(
        system_prompt=SUMMARIZER_INSTRUCTIONS,
        prompt=human_message_content
    )

    logger.info(f"[contentSummarize_activity] Response: {response[:50]}")
    logger.info(f"[contentSummarize_activity] End Activity")
    return response


# python3 -m src.activity.contentSummarize_activity
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    web_result = """
Sources:

Source: Durable Functions のベスト プラクティスと診断ツール
===
URL: https://learn.microsoft.com/ja-jp/azure/azure-functions/durable/durable-functions-best-practice-reference
===
Most relevant content from source: Durable Functions のベスト プラクティスと診断ツール | Microsoft Learn *   Microsoft 365 *   Azure Functions *   Azure Functions *   Durable Functions のドキュメント *   Durable Functions アプリを作成する - C# *   Durable Functions アプリを作成する - JavaScript *   Durable Functions アプリを作成する - TypeScript *   Durable Functions アプリを作成する - Python *   Durable Functions アプリを作成する - PowerShell *   Durable Functions アプリを作成する - Java 4.   デュラブル ファンクションズ (Durable Functions) 4.   デュラブル ファンクションズ (Durable Functions) ### 最新バージョンの Durable Functions 拡張機能と SDK を使用する ### Durable Functions のコード制約に従う Durable Functions API との間で大きな入力と出力をやり取りすると、メモリの問題が発生する可能性があります。 Durable Functions API への入力と出力は、オーケストレーション履歴内へとシリアル化されます。 これは、大きな入力と出力は、時間の経過と共に、オーケストレーター履歴が無限に拡大する大きな要因となり、再生中にメモリ例外を発生させるリスクがあることを意味します。 ### Durable Functions のコンカレンシー設定を微調整する #### Durable Functions 拡張機能 ### Durable Functions 監視拡張機能 *   Durable Functions 拡張機能と .NET プロセス内 SDK *   Java 用の Durable Functions *   JavaScript 用の Durable Functions *   Python 用の Durable Functions
===
Full source content limited to 10000 tokens: この記事では、Durable Functions を使用する際のいくつかのベスト プラクティスについて詳しく説明します。 また、開発、テスト、運用環境での使用中に問題を診断するのに役立つさまざまなツールについて説明します。
ベスト プラクティス
最新バージョンの Durable Functions 拡張機能と SDK を使用する
Durable Functions を実行するために関数アプリで使用するコンポーネントは 2 つあります。 1 つは、対象のプログラミング言語を使用してオーケストレーター、アクティビティ、エンティティの関数を記述できる Durable Functions SDK です。 もう 1 つは "Durable 拡張機能" です。これは、コードを実際に実行するランタイム コンポーネントです。 .NET インプロセス アプリを除き、この SDK と拡張機能は個別にバージョン管理されます。
最新の拡張機能と SDK によって最新状態を保てば、アプリケーションで、最新のパフォーマンスの向上、機能、バグ修正からの利点が得られます。 最新バージョンにアップグレードすると、Microsoft が最新の診断テレメトリを確実に収集できるようにもなり、Azure でサポート ケースを開いたときの調査プロセスを迅速化する助けになります。
Durable Functions のコード制約に従う
オーケストレーター コードの再生動作によって、オーケストレーター関数に記述できるコードの種類に制約が生まれます。 例として、オーケストレーター関数では、再生のたびに同じ結果が生成されるように決定論的 API を使用する必要があるという制約があります。
注意
Durable Functions の Roslyn アナライザーは、C# ユーザーが Durable Functions 固有のコード制約に準拠するようにガイドするライブ コード アナライザーです。 Visual Studio や Visual Studio Code で Roslyn アナライザーを有効にする方法については、「Durable Functions の Roslyn アナライザー」を参照してください。
プログラミング言語の Azure Functions パフォーマンス設定について理解を深める
"既定の設定を使用" すると、選択する言語ランタイムによって関数に厳格なコンカレンシー制限が課される場合があります。 たとえば、特定の VM で実行することが許可される関数は一度に 1 つだけです。 こうした制限は、通常、言語のコンカレンシーとパフォーマンスの設定を "微調整" することで緩和できます。 Durable Functions アプリケーションのパフォーマンスを最適化しようとしている場合は、これらの設定について理解を深める必要があります。
以下は、パフォーマンスとコンカレンシーの設定を微調整すると利点がある場合が多いいくつかの言語の包括的でない一覧と、それを行う場合のガイドラインです。
アプリごとに一意のタスク ハブ名を保証する
複数の Durable Function アプリで同じストレージ アカウントを共有できます。 既定では、アプリの名前がタスク ハブ名として使用されるため、タスク ハブの誤った共有が確実に行われなくなります。 host.json でアプリのタスク ハブ名を明示的に構成する必要がある場合は、名前が "一意" であることを確認する必要があります。 このようにしないと、複数のアプリがメッセージをめぐって競合し、その結果、オーケストレーションが Pending または Running の状態で予期せず "スタック" するなど、未定義の動作が発生する可能性があります。
唯一の例外は、同じアプリの "コピー" を複数のリージョンにデプロイする場合です。この場合、コピーに対して同じタスク ハブを使用できます。
実行中のオーケストレーターにコード変更をデプロイするときにはガイダンスに従う
アプリケーションの存続期間中に関数が追加、削除、変更されることは避けられません。
よくある破壊的変更の例としては、アクティビティやエンティティの関数シグネチャの変更、オーケストレーター ロジックの変更などがあります。 これらの変更は、まだ実行中のオーケストレーションに影響する場合は問題です。 正しくデプロイされていない場合、コードの変更により、非決定論的なエラーでオーケストレーションが失敗し、無期限にスタックしてパフォーマンスが低下するなどの状態に至る可能性があります。実行中のオーケストレーションに影響する可能性のあるコード変更を行うときには、推奨される軽減策を参照してください。
関数の入力と出力は可能な限り小さく保つ
Durable Functions API との間で大きな入力と出力をやり取りすると、メモリの問題が発生する可能性があります。
Durable Functions API への入力と出力は、オーケストレーション履歴内へとシリアル化されます。 これは、大きな入力と出力は、時間の経過と共に、オーケストレーター履歴が無限に拡大する大きな要因となり、再生中にメモリ例外を発生させるリスクがあることを意味します。
API への大きな入力と出力の影響を緩和するために、いくつかの作業をサブオーケストレーターに委任することも選択できます。 これは、履歴のメモリ負荷を 1 つのオーケストレーターから複数のオーケストレーターに負荷分散するのに役立つため、個々の履歴のメモリ占有領域が小さく保たれます。
つまり、"大きな" データを処理するためのベスト プラクティスは、それを外部ストレージに保持し、必要な場合にのみ、そのデータをアクティビティ内で具体化することです。 データ自体を Durable Functions API の入力や出力として通信する代わりにこのアプローチを取ると、アクティビティで必要なときに外部ストレージからそのデータを取得できる軽量な識別子を渡すことができます。
エンティティ データを小さく保つ
Durable Functions API への入力と出力の場合と同様に、エンティティの明示的な状態が大きすぎる場合、メモリの問題が発生する可能性があります。 特に、エンティティ状態は、要求に応じてストレージからシリアル化およびシリアル化解除する必要があるため、状態が大きいと、各呼び出しにシリアル化の待機時間が追加されます。 そのため、エンティティで大規模なデータを追跡する必要がある場合は、データを外部ストレージにオフロードし、必要に応じてストレージからデータを具現化できるエンティティ内の軽量の識別子を追跡することをお勧めします。
Durable Functions のコンカレンシー設定を微調整する
効率を高めるために、1 つのワーカー インスタンスで複数の作業項目を同時に実行できます。 ただし、同時に処理する作業項目が多すぎると、CPU 容量やネットワーク接続などのリソースが枯渇するリスクがあります。多くの場合、作業項目のスケーリングと制限は自動的に処理されるため、これは問題にならないはずです。 とは言え、パフォーマンスの問題 (オーケストレーターが、完了するのに時間がかかりすぎる、保留中でスタックしているなど) が発生している場合や、パフォーマンス テストを行っている場合は、host.json ファイルでコンカレンシーの制限を構成できます。
注意
これは、Azure Functions でお使いの言語ランタイムのパフォーマンスやコンカレンシー設定を微調整する代わりにはなりません。 Durable Functions のコンカレンシー設定では、特定の VM に一度に割り当て可能な作業量のみが決定されますが、VM 内で動作する処理の並列度は決定されません。 後者のためには、言語ランタイムのパフォーマンス設定を微調整する必要があります。
外部イベントに一意の名前を使用する
アクティビティ関数と同様に、外部イベントには "少なくとも 1 回の" 配信保証があります。 つまり、特定の "まれな" 条件 (再起動、スケーリング、クラッシュなどで発生することがあります) で、アプリケーションが同じ外部イベントの重複を受け取ることがあります。 そのため、外部イベントにはオーケストレーターで手動で重複を排除できる ID を含めることをお勧めします。
注意
MSSQL ストレージ プロバイダーは外部イベントを使用し、オーケストレーターの状態をトランザクションとして更新します。そのため、既定の Azure Storage ストレージ プロバイダーとは異なり、そのバックエンドでは重複イベントのリスクはないはずです。 ただし、バックエンド間でコードを移植できるように、外部イベントには一意の名前を付けることをお勧めします。
ストレス テストに投資する
パフォーマンスに関連するものと同様に、アプリの理想的なコンカレンシー設定とアーキテクチャは、最終的にはアプリケーションのワークロードによって異なります。 そのため、予想されるワークロードをシミュレートするパフォーマンス テスト ハーネスに投資し、それを使ってアプリのパフォーマンスと信頼性の実験を実行することをユーザーにお勧めします。
入力、出力、例外における機密データを回避する
Durable Functions API への入出力 (例外を含む) は、選択したストレージ プロバイダーに永続的に保存されます。 これらの入力、出力、または例外に機密データ (秘密情報、接続文字列、個人を特定できる情報など) が含まれている場合、ストレージ プロバイダーのリソースに読み取りアクセスできるユーザーである場合は、それらを入手できます。 機密データを安全に扱うには、アクティビティ関数内で、Azure Key Vault または環境変数からデータを取得し、そのデータをオーケストレーターやエンティティに直接通信しないことが推奨されます。 これにより、機密データがストレージ リソースに漏れるのを防ぐことができます。
注意
このガイダンスは CallHttp オーケストレーター API にも適用され、その要求と応答のペイロードもストレージに永続化されます。 対象となる HTTP エンドポイントに認証が必要で、それが機密である可能性がある場合は、ユーザーがアクティビティ内で HTTP 呼び出しを実装するか、CallHttp で提供される埋め込みのマネージド ID のサポートを使用することをお勧めします。
ヒント
同様に、(Application Insights などで) シークレットを含むデータをログに記録しないようにしてください。ログを読み取ることができるユーザーであれば、シークレットを入手できます。
問題の診断に役立つツールがいくつかあります。
Durable Functions と Durable Task Framework のログ
Durable Functions 拡張機能
Durable 拡張機能では、オーケストレーションの実行をエンドツーエンドでトレースできる追跡イベントが生成されます。 これらの追跡イベントは、Azure portal で Application Insights 分析ツールを使って検出および照会できます。 生成される追跡データの詳細レベルは、host.json ファイルの logger (Functions 1.x) または logging (Functions 2.0) セクションで構成できます。
構成の詳細を参照してください。
デュラブル タスク フレームワーク
Durable 拡張機能の v 2.3.0 以降では、基になる Durable Task Framework (DTFx) によって出力されたログもコレクションに使用できます。
これらのログを有効にする方法の詳細を参照してください。
Azure Portal
問題の診断と解決
Azure Functions アプリ診断は、Azure portal にある、アプリケーションの潜在的な問題を監視して診断するための便利なリソースです。 診断に基づく問題の解決に役立つ提案も提供されます。 「Azure Function アプリ診断」を参照してください。
Durable Functions オーケストレーション トレース
Azure portal には、各オーケストレーション インスタンスの状態を理解し、エンドツーエンドの実行をトレースするのに役立つオーケストレーション トレースの詳細が用意されています。 Azure Functions アプリ内の関数の一覧を確認すると、トレースへのリンクが含まれる [モニター] 列が表示されます。 お使いのアプリでこの情報を取得するには、Applications Insights を有効にする必要があります。
Durable Functions 監視拡張機能
これは、オーケストレーション インスタンスを監視、管理、デバッグするための UI を提供する Visual Studio Code 拡張機能です。
Roslyn アナライザー
Durable Functions の Roslyn アナライザーは、C# ユーザーが Durable Functions 固有のコード制約に準拠するようにガイドするライブ コード アナライザーです。 Visual Studio や Visual Studio Code で Roslyn アナライザーを有効にする方法については、「Durable Functions の Roslyn アナライザー」を参照してください。
サポート
質問とサポートについては、以下のいずれかの GitHub リポジトリでイシューを開くことができます。 Azure のバグを報告する場合は、影響を受けたインスタンスの ID、問題を示している時間範囲 (UTC)、アプリケーション名 (可能な場合)、デプロイ リージョンなどの情報を含めると、調査が大幅にスピードアップされます。

Source: The Ultimate Guide to Azure Durable Functions: A Deep Dive into ...
===
URL: https://medium.com/@robertdennyson/the-ultimate-guide-to-azure-durable-functions-a-deep-dive-into-long-running-processes-best-bacc53fcc6ba
===
Most relevant content from source: The Ultimate Guide to Azure Durable Functions: A Deep Dive into Long-Running Processes, Best Practices, and Comparisons with Azure Batch | by Robert Dennyson | Medium Azure Durable Functions is an extension of Azure Functions, allowing you to write stateful workflows in a serverless environment. Behind the scenes, Durable Functions use Azure Storage to manage the state, checkpoints, and history of function executions: FeatureAzure Durable FunctionsAzure BatchExecution ModelEvent-driven, serverless, statefulManaged batch processing, designed for parallel tasksIdeal Use CaseLong-running workflows with checkpoints & orchestrationHigh-performance computing tasks, large-scale parallelismState ManagementUses Azure Storage for state persistenceNo built-in state managementScalabilityServerless auto-scalingManually scalable to handle large batch workloadsCost ModelConsumption-based billingVM-based billing (pay for allocated VMs) Azure Durable Functions is a powerful, flexible, and stateful solution for orchestrating long-running workflows in a serverless environment.
===
Full source content limited to 10000 tokens: The Ultimate Guide to Azure Durable Functions: A Deep Dive into Long-Running Processes, Best Practices, and Comparisons with Azure BatchIntroductionAs cloud computing has evolved, the demand for handling long-running workflows and processes in an efficient, cost-effective manner has grown. Microsoft Azure offers two compelling solutions to this challenge: Azure Durable Functions and Azure Batch. Both services provide robust options for different types of workloads, but they cater to different use cases. This article aims to provide a detailed explanation of Azure Durable Functions — how they work, when to use them, and how they compare to Azure Batch. We’ll also include code examples to illustrate how to implement durable functions effectively.What Are Azure Durable Functions?Azure Durable Functions is an extension of Azure Functions, allowing you to write stateful workflows in a serverless environment. In contrast to the stateless nature of standard Azure Functions, Durable Functions manage the state, enabling you to create workflows that can run for days, weeks, or even longer.Key Characteristics of Durable Functions:Stateful: Retains state information across function executions.Serverless: Leverages Azure’s serverless architecture, scaling as needed.Reliable: Ensures long-running workflows are fault-tolerant.Event-driven: Reacts to external events and triggers.How Durable Functions Work1. Request Handling and Execution FlowWhen a request is received by a Durable Function, the orchestration process begins. Here’s a step-by-step breakdown:Client Function Invocation: The process starts with a client function that triggers the orchestration. This client function could be an HTTP trigger, a queue trigger, or even a time trigger.Orchestrator Function Execution: The client function starts an orchestrator function, which defines the workflow logic. Unlike regular functions, orchestrator functions execute step by step in a way that allows them to pause, wait for an external event, or resume based on certain conditions.Activity Functions Execution: The orchestrator function calls activity functions that perform individual tasks within the workflow. Each activity function is executed as needed, and its status is stored in Azure Storage Tables and Queues.2. Durable Task ManagementBehind the scenes, Durable Functions use Azure Storage to manage the state, checkpoints, and history of function executions:Storage Queues: Each step’s progress is stored as a message in Azure Storage Queues, enabling the orchestrator to process tasks sequentially or in parallel.Storage Tables: Execution history, input parameters, and state data are stored in Azure Storage Tables for easy retrieval and auditing.3. Checkpointing and Replay MechanismOne of the unique features of Durable Functions is the checkpoint and replay mechanism. This mechanism ensures that the orchestrator can reconstruct the state of the workflow, even after an interruption (e.g., a server crash or a deployment). The orchestrator replays the workflow from the last checkpoint, using the stored execution history in Azure Storage.This capability makes Durable Functions ideal for handling long-running workflows that span hours, days, or even weeks.Types of Durable Functions1. Orchestrator FunctionsThe heart of a Durable Function workflow. It defines the orchestration logic that manages activity functions, sub-orchestrations, and external events.Use Case: Complex workflows requiring multiple steps, such as processing orders or managing approvals.Example:[FunctionName("OrchestratorFunction")]public static async Task RunOrchestrator(    [OrchestrationTrigger] IDurableOrchestrationContext context){    var result1 = await context.CallActivityAsync<string>("ActivityFunction1", "input1");    var result2 = await context.CallActivityAsync<string>("ActivityFunction2", result1);    return result2;}2. Activity FunctionsPerform discrete tasks as part of the overall workflow. These are called by the orchestrator function.Use Case: Individual tasks that are part of a broader workflow, like processing an image, sending an email, or querying a database.Example:[FunctionName("ActivityFunction1")]public static string SayHello([ActivityTrigger] string name, ILogger log){    log.LogInformation($"Saying hello to {name}.");    return $"Hello {name}!";}3. Entity FunctionsManage state explicitly, similar to an object in object-oriented programming. They allow you to store state across invocations, making them ideal for managing counters, workflows with persistence, and other stateful scenarios.Use Case: Managing shopping carts, counters, or any other scenario requiring state persistence.Example:[FunctionName("Counter")]public static Task Counter([EntityTrigger] IDurableEntityContext ctx){    switch (ctx.OperationName.ToLowerInvariant())    {        case "increment":            ctx.SetState(ctx.GetState<int>() + 1);            break;        case "reset":            ctx.SetState(0);            break;    }    return Task.CompletedTask;}4. Client FunctionsTrigger orchestrator functions and handle communication with them. These functions could be triggered by HTTP requests, queues, or other events.Use Case: Initiating workflows, querying status, or handling user inputs.Example:[FunctionName("StartOrchestration")]public static async Task<IActionResult> StartOrchestration(    [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequest req,    [DurableClient] IDurableOrchestrationClient starter,    ILogger log){    string instanceId = await starter.StartNewAsync("OrchestratorFunction", null);    log.LogInformation($"Started orchestration with ID = '{instanceId}'.");    return starter.CreateCheckStatusResponse(req, instanceId);}Best Use Cases for Each Durable Function TypeOrchestrator Function: Long-running workflows (e.g., ETL processes, order processing, approval workflows).Activity Function: Short, independent tasks (e.g., file processing, sending emails).Entity Function: Scenarios needing durable state (e.g., shopping cart management, counters).Client Function: Triggering and managing orchestrations (e.g., initiating workflows, monitoring status).Azure Durable Functions vs. Azure BatchFeatureAzure Durable FunctionsAzure BatchExecution ModelEvent-driven, serverless, statefulManaged batch processing, designed for parallel tasksIdeal Use CaseLong-running workflows with checkpoints & orchestrationHigh-performance computing tasks, large-scale parallelismState ManagementUses Azure Storage for state persistenceNo built-in state managementScalabilityServerless auto-scalingManually scalable to handle large batch workloadsCost ModelConsumption-based billingVM-based billing (pay for allocated VMs)When to Use Each ServiceUse Azure Durable Functions When:You need to manage stateful workflows.Long-running, multi-step processes with checkpoints are required.Event-driven orchestration is needed.Use Azure Batch When:You have large-scale, parallelizable tasks (e.g., image rendering, scientific computations).You need fine-grained control over the underlying compute resources.Practical Example: Long-Running Order Processing WorkflowDurable Function Code Example:[FunctionName("OrderProcessingOrchestrator")]public static async Task OrderProcessingOrchestrator(    [OrchestrationTrigger] IDurableOrchestrationContext context){    var orderId = context.GetInput<string>();    await context.CallActivityAsync("ValidateOrder", orderId);    await context.CallActivityAsync("ProcessPayment", orderId);    await context.CallActivityAsync("ShipOrder", orderId);    await context.CallActivityAsync("SendConfirmation", orderId);}Activity Functions:[FunctionName("ValidateOrder")]public static async Task ValidateOrder([ActivityTrigger] string orderId, ILogger log){    log.LogInformation($"Validating order {orderId}");    // Validation logic}[FunctionName("ProcessPayment")]public static async Task ProcessPayment([ActivityTrigger] string orderId, ILogger log){    log.LogInformation($"Processing payment for order {orderId}");    // Payment processing logic}[FunctionName("ShipOrder")]public static async Task ShipOrder([ActivityTrigger] string orderId, ILogger log){    log.LogInformation($"Shipping order {orderId}");    // Shipping logic}[FunctionName("SendConfirmation")]public static async Task SendConfirmation([ActivityTrigger] string orderId, ILogger log){    log.LogInformation($"Sending confirmation for order {orderId}");    // Send confirmation logic}ConclusionAzure Durable Functions is a powerful, flexible, and stateful solution for orchestrating long-running workflows in a serverless environment. It’s ideal for scenarios that require managing state, handling complex workflows, and reacting to external events over time. Azure Batch, on the other hand, excels in handling high-performance, parallel, and large-scale batch processing tasks.By understanding the differences and strengths of each service, you can choose the right solution for your specific workload, ensuring optimal performance, scalability, and cost-effectiveness.

Source: Durable Functions best practices and diagnostic tools | Microsoft Learn
===
URL: https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-best-practice-reference
===
Most relevant content from source: Best practices · Use the latest version of the Durable Functions extension and SDK · Adhere to Durable Functions code constraints · Familiarize
===
Full source content limited to 10000 tokens: This article details some best practices when using Durable Functions. It also describes various tools to help diagnose problems during development, testing, and production use.
Best practices
Use the latest version of the Durable Functions extension and SDK
There are two components that a function app uses to execute Durable Functions. One is the Durable Functions SDK that allows you to write orchestrator, activity, and entity functions using your target programming language. The other is the Durable extension, which is the runtime component that actually executes the code. With the exception of .NET in-process apps, the SDK and the extension are versioned independently.
Staying up to date with the latest extension and SDK ensures your application benefits from the latest performance improvements, features, and bug fixes. Upgrading to the latest versions also ensures that Microsoft can collect the latest diagnostic telemetry to help accelerate the investigation process when you open a support case with Azure.
See Upgrade durable functions extension version for instructions on getting the latest extension version.
To ensure you're using the latest version of the SDK, check the package manager of the language you're using.
The replay behavior of orchestrator code creates constraints on the type of code that you can write in an orchestrator function. An example of a constraint is that your orchestrator function must use deterministic APIs so that each time it’s replayed, it produces the same result.
Note
The Durable Functions Roslyn Analyzer is a live code analyzer that guides C# users to adhere to Durable Functions specific code constraints. See Durable Functions Roslyn Analyzer for instructions on how to enable it on Visual Studio and Visual Studio Code.
Familiarize yourself with your programming language's Azure Functions performance settings
Using default settings, the language runtime you select may impose strict concurrency restrictions on your functions. For example: only allowing 1 function to execute at a time on a given VM. These restrictions can usually be relaxed by fine tuning the concurrency and performance settings of your language. If you're looking to optimize the performance of your Durable Functions application, you will need to familiarize yourself with these settings.
Below is a non-exhaustive list of some of the languages that often benefit from fine tuning their performance and concurrency settings, and their guidelines for doing so.
Guarantee unique Task Hub names per app
Multiple Durable Function apps can share the same storage account. By default, the name of the app is used as the task hub name, which ensures that accidental sharing of task hubs won't happen. If you need to explicitly configure task hub names for your apps in host.json, you must ensure that the names are unique. Otherwise, the multiple apps will compete for messages, which could result in undefined behavior, including orchestrations getting unexpectedly "stuck" in the Pending or Running state.
The only exception is if you deploy copies of the same app in multiple regions; in this case, you can use the same task hub for the copies.
Follow guidance when deploying code changes to running orchestrators
It's inevitable that functions will be added, removed, and changed over the lifetime of an application. Examples of common breaking changes include changing activity or entity function signatures and changing orchestrator logic. These changes are a problem when they affect orchestrations that are still running. If deployed incorrectly, code changes could lead to orchestrations failing with a non-deterministic error, getting stuck indefinitely, performance degradation, etc. Refer to recommended mitigation strategies when making code changes that may impact running orchestrations.
Keep function inputs and outputs as small as possible
You can run into memory issues if you provide large inputs and outputs to and from Durable Functions APIs.
Inputs and outputs to Durable Functions APIs are serialized into the orchestration history. This means that large inputs and outputs can, over time, greatly contribute to an orchestrator history growing unbounded, which risks causing memory exceptions during replay.
To mitigate the impact of large inputs and outputs to APIs, you may choose to delegate some work to sub-orchestrators. This helps load balance the history memory burden from a single orchestrator to multiple ones, therefore keeping the memory footprint of individual histories small.
That said the best practice for dealing with large data is to keep it in external storage and to only materialize that data inside Activities, when needed. When taking this approach, instead of communicating the data itself as inputs and/or outputs of Durable Functions APIs, you can pass in some lightweight identifier that allows you to retrieve that data from external storage when needed in your Activities.
Keep Entity data small
Just like for inputs and outputs to Durable Functions APIs, if an entity's explicit state is too large, you may run into memory issues. In particular, an Entity state needs to be serialized and de-serialized from storage on any request, so large states add serialization latency to each invocation. Therefore, if an Entity needs to track large data, it's recommended to offload the data to external storage and track some lightweight identifier in the entity that allows you to materialize the data from storage when needed.
Fine tune your Durable Functions concurrency settings
A single worker instance can execute multiple work items concurrently to increase efficiency. However, processing too many work items concurrently risks exhausting resources like CPU capacity, network connections, etc. In many cases, this shouldn’t be a concern because scaling and limiting work items are handled automatically for you. That said, if you’re experiencing performance issues (such as orchestrators taking too long to finish, are stuck in pending, etc.) or are doing performance testing, you could configure concurrency limits in the host.json file.
Note
This is not a replacement for fine-tuning the performance and concurrency settings of your language runtime in Azure Functions. The Durable Functions concurrency settings only determine how much work can be assigned to a given VM at a time, but it does not determine the degree of parallelism in processing that work inside the VM. The latter requires fine-tuning the language runtime performance settings.
Use unique names for your external events
As with activity functions, external events have an at-least-once delivery guarantee. This means that, under certain rare conditions (which may occur during restarts, scaling, crashes, etc.), your application may receive duplicates of the same external event. Therefore, we recommend that external events contain an ID that allows them to be manually de-duplicated in orchestrators.
Note
The MSSQL storage provider consumes external events and updates orchestrator state transactionally, so in that backend there should be no risk of duplicate events, unlike with the default Azure Storage storage provider. That said, it is still recommended that external events have unique names so that code is portable across backends.
Invest in stress testing
As with anything performance related, the ideal concurrency settings and architecture of your app ultimately depends on your application's workload. Therefore, it's recommended that users to invest in a performance testing harness that simulates their expected workload and to use it to run performance and reliability experiments for their app.
Avoid sensitive data in inputs, outputs, and exceptions
Inputs and outputs (including exceptions) to and from Durable Functions APIs are durably persisted in your storage provider of choice. If those inputs, outputs, or exceptions contain sensitive data (such as secrets, connection strings, personally identifiable information, etc.) then anyone with read access to your storage provider's resources would be able to obtain them. To safely deal with sensitive data, it is recommended for users to fetch that data within activity functions from either Azure Key Vault or environment variables, and to never communicate that data directly to orchestrators or entities. That should help prevent sensitive data from leaking into your storage resources.
Note
This guidance also applies to the CallHttp orchestrator API, which also persists its request and response payloads in storage. If your target HTTP endpoints require authentication, which may be sensitive, it is recommended that users implement the HTTP Call themselves inside of an activity, or to use the built-in managed identity support offered by CallHttp, which does not persist any credentials to storage.
Tip
Similarly, avoid logging data containing secrets as anyone with read access to your logs (for example in Application Insights), would be able to obtain those secrets.
There are several tools available to help you diagnose problems.
Durable Functions and Durable Task Framework Logs
Durable Functions Extension
The Durable extension emits tracking events that allow you to trace the end-to-end execution of an orchestration. These tracking events can be found and queried using the Application Insights Analytics tool in the Azure portal. The verbosity of tracking data emitted can be configured in the logger (Functions 1.x) or logging (Functions 2.0) section of the host.json file. See configuration details.
Durable Task Framework
Starting in v2.3.0 of the Durable extension, logs emitted by the underlying Durable Task Framework (DTFx) are also available for collection. See details on how to enable these logs.
Azure portal
Diagnose and solve problems
Azure Function App Diagnostics is a useful resource on Azure portal for monitoring and diagnosing potential issues in your application. It also provides suggestions to help resolve problems based on the diagnosis. See Azure Function App Diagnostics.
Durable Functions Orchestration traces
Azure portal provides orchestration trace details to help you understand the status of each orchestration instance and trace the end-to-end execution. When you look at the list of functions inside your Azure Functions app, you'll see a Monitor column that contains links to the traces. You need to have Applications Insights enabled for your app to get this information.
Durable Functions Monitor Extension
This is a Visual Studio Code extension that provides a UI for monitoring, managing, and debugging your orchestration instances.
Roslyn Analyzer
The Durable Functions Roslyn Analyzer is a live code analyzer that guides C# users to adhere to Durable Functions specific code constraints. See Durable Functions Roslyn Analyzer for instructions on how to enable it on Visual Studio and Visual Studio Code.
Support
For questions and support, you may open an issue in one of the GitHub repos below. When reporting a bug in Azure, including information such as affected instance IDs, time ranges in UTC showing the problem, the application name (if possible) and deployment region will greatly speed up investigations.
"""

    test_input_data = {
        "topic": "Durable Functions って何？",
        "existing_summary": "",
        "recent_web_research_result": web_result
    }

    asyncio.run(contentSummarize_activity(test_input_data))
