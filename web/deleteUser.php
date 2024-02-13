<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    session_start();

    if(isset($_SESSION['userId'])) $userId = $_SESSION['userId'];
    else header("location:./main.phtml");  // 로그인 x => 메인으로 강제 이동

    require_once "web_db.php";  # db
    $conndb = conndb();

    if(isset($_POST['userId'])) $userIdInput = $_POST["userId"];
    else header("location:./main.phtml");  
    
    if($userIdInput != $userId){
        header("location:./main.phtml");  // 다른 계정으로 삭제하지 못하게
    }

    $sqlStr = "DELETE FROM user WHERE id='$userId'";
    $result = mysqli_query($conndb, $sqlStr);

    header("location:./logout.php");
?>