// 键盘映射
const NUM_KEY = {
    "1": [380, 2386],
    "2": [684, 2366],
    "3": [989, 2370],
    "4": [399, 2587],
    "5": [684, 2603],
    "6": [985, 2595],
    "7": [375, 2804],
    "8": [684, 2804],
    "9": [985, 2804],
    "0": [688, 3022]
};

// 解锁相关函数
function needUnlock() {
    // 常见锁屏特征
    return (
        text("仅可紧急通话").exists() ||
        textContains("密码").exists() ||
        textContains("PIN").exists() ||
        desc("0").exists() || text("0").exists()
    );
}

// 键盘输入函数
function inputNumberByKeyboard(num) {
    let s = String(num);
    for (let c of s) {
        let p = NUM_KEY[c];
        if (!p) {
            console.log("❌ 未找到键位: " + c);
            continue;
        }
        click(p[0], p[1]);
        sleep(50);
    }
}


// 买入函数
function AddStock(stockCode) {
    console.log("ready buy", stockCode);

    // 2️⃣ 输入股票代码
    // setText(stockCode);
    // sleep(3000);
    inputNumberByKeyboard(stockCode);
    sleep(1500);

    // 4️⃣ 点击添加按钮
    click(1344, 620);   // 买入数量区域
    sleep(1500);


    // 删除代码，方便下一次输入
    for (let i = 0; i < stockCode.length; i++) {
        click(1293, 2492); // 点击"删除"键，模拟删除
        sleep(50);
    }

}


"auto";

// 1️⃣ 等待无障碍
auto.waitFor();
console.log("无障碍已就绪");


// 2️⃣ 点亮屏幕
if (!device.isScreenOn()) {
    device.wakeUp();
    console.log("已点亮屏幕");
}
sleep(500);


// 3️⃣ 上滑进入解锁界面
swipe(device.width / 2, device.height * 0.8, device.width / 2, device.height * 0.2, 300);
sleep(500);

// 4️⃣ 输入解锁密码（示例：1234）
// ⚠️ 根据你的手机密码修改
if (needUnlock()) {
    console.log("Lock screen, start entering password");

    let password = "4014";
    for (let i = 0; i < password.length; i++) {
        click(password[i]);
        sleep(200);
    }

    sleep(100);
    console.log("Unlock");
} else {
    console.log("No lock screen, skipping password input");
}

// 5️⃣ 启动微信
app.launchApp("国信金太阳");
console.log("starting app...");
sleep(500);

// 6️⃣ 点击【我的】
// 方式一：文字（最稳）
let myBtn = text("行情").findOne(500);
if (myBtn) {
    myBtn.click();
    console.log("click trade");
} else {
    console.log("no find trade");
    // 方式二：坐标兜底（右下角）
    click(451, 3032);
}

// 清理股票
let cleanBtn = text("编辑股票").findOne(500);
if (cleanBtn) {
    cleanBtn.click();
    console.log("click edit stocks");
} else {
    console.log("no find edit stocks");
    // 方式二：坐标兜底（右下角）
    click(168, 1307);
}

let allBtn = text("全选").findOne(500);
if (allBtn) {
    allBtn.click();
    console.log("click select all");
} else {
    console.log("no find select all");
    // 方式二：坐标兜底（右下角）
    click(201, 3078);
}

let deleteBtn = text("删除").findOne(500);
if (deleteBtn) {
    deleteBtn.click();
    console.log("click delete stocks");
} else {
    console.log("no find delete stocks");
    // 方式二：坐标兜底（右下角）
    click(1200, 3078);
}

let confirmBtn = text("确定").findOne(500);
if (confirmBtn) {
    confirmBtn.click();
    console.log("click confirm delete");
} else {
    console.log("no find confirm delete");
    // 方式二：坐标兜底（右下角）
    click(1200, 3078);
}

let completedBtn = text("完成").findOne(500);
if (completedBtn) {
    completedBtn.click();
    console.log("click completed");
} else {
    console.log("no find completed");
    // 方式二：坐标兜底（右下角）
    click(1304, 208);
}

// 添加股票
// -----------------发送 POST 请求到服务器-----------------
var payload = {};
let url = "http://192.168.14.245:30003/reference";
let res = http.postJson(url, payload, {timeout:200000});

if (!res || res.statusCode !== 200) {
    toast("请求失败");
    exit();
}
// 解析返回的 JSON
let str = res.body.string();
// 把结果打印出来，方便调试
log("服务器返回的原始字符串:", str);



// -----------------解析结果并把参考的gp添加到列表中-----------------
let result;
try {
    result = JSON.parse(str);
} catch (e) {
    toast("解析JSON失败");
    log(e);
    exit();
}

// result = { data: [ { code: 688229, name: "博睿数据", price: 99.0, amount: 100 } ],benjin: 94.87 }
// result.data 就是列表

let data = result.data;

// 1️⃣ 点击股票代码搜索框
click(1353, 164);
sleep(500);

for (let i = 0; i < data.length; i++) {
    let row = data[i];

    let code = row["代码"];

    if (!code) {
        console.log("Skip invalid data:", JSON.stringify(row));
        continue;
    }

    console.log("Deal With", i + 1);
    AddStock(code);

    // 防止过快操作（非常重要）
    sleep(500);
}

// 广告位：715，2308
