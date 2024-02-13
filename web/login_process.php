<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    session_start();

    require_once "web_db.php";  # db
    $conndb = conndb();

    $userId = $_POST["username"];
    $userPw = $_POST["password"];
    $userPwCrypt = crypt($userPw, $userPw);  # 비밀번호 암호화

    $sqlStr = "SELECT password, langCode FROM user WHERE id='$userId'";
    $result = mysqli_query($conndb, $sqlStr);

    $resultPw = mysqli_fetch_row($result);

    if($resultPw[0] == $userPwCrypt){
        $_SESSION['userId'] = $userId;
        $_SESSION['langCode'] = $resultPw[1];
        header("location:./main.phtml");
    }
    else{
        header("location:./login.phtml?error=1");
    }
?>