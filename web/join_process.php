<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    require_once "web_db.php";  # db
    $conndb = conndb();

    $userId = $_POST["username"];
    $userPw = $_POST["password1"];
    $userPwCrypt = crypt($userPw, $userPw);  # 비밀번호 암호화

    $sqlStr = "INSERT INTO user(id, password) VALUES('$userId', '$userPwCrypt')";
    mysqli_query($conndb, $sqlStr);

    header("location:./welcome.phtml")
?>