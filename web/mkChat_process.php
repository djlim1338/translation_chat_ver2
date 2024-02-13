<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    function rChatId($maxNum){
        $rCase = 0;
        $rNum = mt_rand(65,90);
        $rChar = chr($rNum);
        for($i=1; $i<$maxNum; $i++){
            $rCase = mt_rand(0,1);
            switch($rCase){
                case 0: // 숫자 0~9 넣음. 물론 char형
                    $rNum = mt_rand(48,57);
                    $rChar = $rChar.chr($rNum);
                    break;
                case 1: // 대문자 A~Z
                    $rNum = mt_rand(65,90);
                    $rChar = $rChar.chr($rNum);
                    break;
            }
        }
        return $rChar;
    }

    session_start();
    /*
    $userId = $_SESSION['userId'];
    if($userId == '' || $userId == null){
        header("location:./main.phtml");  // 로그인 x => 메인으로 강제 이동
    }
    */
    if(isset($_SESSION['userId'])) $userId = $_SESSION['userId'];
    else header("location:./main.phtml");

    require_once "web_db.php";  # db
    $conndb = conndb();

    $userId = $_SESSION["userId"];
    $chatName = $_POST["chatRoomName"];
    if(isset($_POST["openState"])) $chatOpenState = 0;
    else $chatOpenState = 1;

    do{
        $chatId=rChatId(16);
        $sqlStr="SELECT * FROM chatRoom WHERE roomId='".$chatId."'";
        $result=mysqli_query($conndb, $sqlStr);
        $num_rows=mysqli_num_rows($result);
    }while($num_rows!=0);
    echo $chatId;

    $sqlStr = "INSERT INTO chatRoom VALUES('$chatId', '$chatName', $chatOpenState, '$userId')";
    $result = mysqli_query($conndb, $sqlStr);

    $sqlStr = "INSERT INTO userChatLink VALUES('$chatId', '$userId')";
    $result = mysqli_query($conndb, $sqlStr);

    header("location:./main.phtml");
?>