<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    session_start();

    if(isset($_SESSION['userId'])) $userId = $_SESSION['userId'];
    else header("location:./main.phtml");  // 로그인 x => 메인으로 강제 이동

    require_once "web_db.php";  # db
    $conndb = conndb();

    if(isset($_POST['chatId'])) $chatIdInput = $_POST["chatId"];
    else header("location:./main.phtml");  
    
    $sqlStr = "SELECT masterId FROM chatRoom WHERE id='$chatIdInput'";
    $result = mysqli_query($conndb, $sqlStr);
    $row = mysqli_fetch_assoc($result);
    $masterId = $row['masterId'];

    if($masterId != $userId) header("location:./main.phtml");  // 방의 주인이 아닌경우 => 메인으로 강제 이동

    $sqlStr = "DELETE FROM chatRoom WHERE id='$chatIdInput'";
    $result = mysqli_query($conndb, $sqlStr);

    header("location:./main.phtml");
?>