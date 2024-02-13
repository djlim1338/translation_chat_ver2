<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    session_start();

    require_once "web_db.php";  # db
    $conndb = conndb();

    if(isset($_POST["langCode"])) $langCode = $_POST["langCode"];
    else header("location:./translation_list.phtml?error=1");
    if(isset($_SESSION["userId"])) $userId = $_SESSION["userId"];
    else header("location:./translation_list.phtml?error=1");

    $sqlStr = "UPDATE user SET langCode='".$langCode."' WHERE id='".$userId."'";
    mysqli_query($conndb, $sqlStr);
    $_SESSION['langCode'] = $langCode;

    header("location:./translation_list.phtml?error=0");
?>