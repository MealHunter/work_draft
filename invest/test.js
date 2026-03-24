// //文件路径
// var path = "/storage/emulated/0/脚本/result.json";
// //打开文件
// var file = open(path);
// //读取文件的所有内容
// var text = file.read();
// //打印到控制台
// print(text);
// //关闭文件
// file.close();
// console.show();



let url = "http://192.168.14.245:8000/buy";
var path = "/storage/emulated/0/脚本/result.json";
var file = open(path);
var text = file.read();
file.close();
// 解析 JSON 字符串为对象
var payload;
try {
    payload = JSON.parse(text);
} catch (e) {
    toast("解析 JSON 失败");
    log(e);
    exit();
}

let res = http.postJson(url, payload,{timeout:120000});

if (!res || res.statusCode !== 200) {
    toast("请求失败");
    exit();
}

let str = res.body.string();
log(str);

