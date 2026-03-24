// 键盘映射
const NUM_KEY = {
    "1": [409, 2505],
    "2": [734, 2521],
    "3": [1007, 2499],
    "4": [422, 2678],
    "5": [719, 2688],
    "6": [996, 2680],
    "7": [378, 2873],
    "8": [720, 2862],
    "9": [1000, 2876],
    "0": [683, 3071]
};

function needUnlock() {
    // 常见锁屏特征
    return (
        text("仅可紧急通话").exists() ||
        textContains("密码").exists() ||
        textContains("PIN").exists() ||
        desc("0").exists() || text("0").exists()
    );
}

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

function sellStock(stockCode, quantity) {
    console.log("ready sell", stockCode, "amount:", quantity);

    // 1️⃣ 点击股票代码输入框
    click(670, 672);
    sleep(2000);

    // 2️⃣ 输入股票代码
    inputNumberByKeyboard(stockCode);
    sleep(2000);

    // 3️⃣ 找到"卖出数量"输入框并点击
    click(735, 1225);
    sleep(100);

    // 4️⃣ 用虚拟键盘输入数量
    inputNumberByKeyboard(quantity);
    sleep(2000);

    // 5️⃣ 点击卖出按钮
    let sellBtns = text("卖出").find();
    if (sellBtns.size() > 0) {
        sellBtns.get(sellBtns.size() - 1).click();
        console.log("✅ 点击最后一个【卖出】");
        sleep(1500);
    }
    sleep(1500);

    // 6️⃣ 确认卖出（如果有确认按钮）
    let confirmBtn = textContains("确认卖出").findOne(3000);
    if (confirmBtn) {
        confirmBtn.click();
        console.log("✅ 卖出确认完成：", stockCode);
        sleep(1500);
    } else {
        console.log("⚠️ 未出现确认按钮，可能已自动成交");
    }

    sleep(1500);

    let buyAnother = textContains("再委托一笔").findOne(3000);
    if (buyAnother) {
        buyAnother.click();
        console.log("✅ 点击【再委托一笔】继续下一笔");
        sleep(1500);
    }else{
        console.log("⚠️ 未找到【再委托一笔】，使用坐标点击继续");
        click(1049, 1706);
    }
}


//--------------------- 卖出操作 --------------------
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

// 2️⃣ 从左向右滑动解锁（如果有锁屏）
// if (needUnlock()) {
//     swipe(device.width * 0.3, device.height * 0.8, device.width * 0.8, device.height * 0.8, 300);
//     sleep(1000);
// }else{
//     console.log("未检测到滑动解锁界面，跳过滑动操作");
// }


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
sleep(2000);

// 6️⃣ 点击【交易】
// 方式一：文字（最稳）
let myBtn = text("交易").findOne(5000);
if (myBtn) {
    myBtn.click();
    console.log("click trade");
} else {
    console.log("no find trade");
    // 方式二：坐标兜底（右下角）
    // click(720, 3039);
}


// 卖出操作
let buyBtn = text("卖出").findOne(5000);
if (buyBtn) {
    buyBtn.click();
    console.log("click sell");
} else {
    console.log("no find sell");
    click(566, 1314);
}


// -----------------读取本地的 JSON 文件（持仓数据）------------------
var path = "/storage/emulated/0/脚本/result.json";
var file = open(path);
var fileContent = file.read();
file.close();

// 解析 JSON 字符串为对象
var payload;
try {
    payload = JSON.parse(fileContent);
} catch (e) {
    toast("解析 JSON 失败");
    log(e);
    exit();
}
log("解析后的 JSON对象:", payload);

// 保存原始持仓数据（用于后续卖出操作）
var originalHoldings = payload.data || [];

// -----------------调用 /sell API------------------
let url = "http://192.168.14.245:8000/sell";
let res = http.postJson(url, payload, {timeout: 200000});

if (!res || res.statusCode !== 200) {
    toast("请求失败");
    exit();
}

// 解析返回的 JSON
let str = res.body.string();

// 把结果打印出来，方便调试，同时更新本地文件
log("服务器返回的原始字符串:", str);
var file = open(path, 'w');
file.write(str);
file.close();

let sellResult;
try {
    sellResult = JSON.parse(str);
} catch (e) {
    toast("解析JSON失败");
    log(e);
    exit();
}

// -----------------执行卖出操作------------------
// 使用原始持仓数据执行卖出（因为 API 返回的 data 是空的）
let data = originalHoldings;

if (!data || data.length === 0) {
    console.log("没有持仓需要卖出");
    console.log("当前本金:", sellResult.benjin);
    exit();
}

for (let i = 0; i < data.length; i++) {
    let row = data[i];

    let code = row["code"];
    let qty = parseInt(row["amount"], 10);

    if (!code || !qty || qty <= 0) {
        console.log("Skip invalid data:", JSON.stringify(row));
        continue;
    }

    console.log("Deal With", i + 1);
    sellStock(code, qty);

    // 防止过快操作（非常重要）
    sleep(1500);
}

console.log("全部卖出完成，当前本金:", sellResult.benjin);


