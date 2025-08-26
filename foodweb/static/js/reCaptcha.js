
function onSubmit(token) {
alert("HELLO");
 document.getElementById("demo-form").submit();
 alert("HELLO 1");
}


//function onClick(e) {
//    grecaptcha.ready(function() {
//        alert("ALO 0");
//
//          grecaptcha.execute('6LequfgkAAAAANl1Q3A-bKNvwLoGJcrqpfcQH7R4', {action: 'submit'}).then(function(token) {
//              // Add your logic to submit to your backend server here.
//              alert("ALO 1");
//
//            var form = document.querySelector('#demo-form');
//            var formData = new FormData(form);
//            alert("ALO 2");
//            // Thêm mã thông báo (token) vào dữ liệu biểu mẫu để gửi đến máy chủ
//            formData.append('recaptcha_token', token);
//            alert("ALO 3");
//            alert(token)
////
//            // Tạo yêu cầu HTTP POST đến máy chủ của bạn để xử lý dữ liệu
//            fetch('/login', {
//              method: 'POST',
//              body: formData
//            }).then(function(response) {
//            }
//              // Xử lý phản hồi từ máy chủ của bạn
//              console.log(response);
//
//              document.getElementById("demo-form").submit();
//          });
//    });
//}

//==============================================================================

//function onSubmit(e) {
//    function onSubmit(token) {
//        // Gửi yêu cầu POST đến API của Google để xác minh token
//        fetch(`/login`, {
//          method: 'POST',
//          headers: {
//            'Content-Type': 'application/x-www-form-urlencoded'
//          },
//          body: 'token=' + token
//        })
//        .then(function(response) {
//          // Xử lý phản hồi từ API của Google
//          if (response.ok) {
//            // Nếu xác minh thành công, cho phép người dùng truy cập trang web của bạn
//            console.log('reCAPTCHA verification successful!');
//          } else {
//            // Nếu xác minh không thành công, yêu cầu người dùng hoàn thành lại reCAPTCHA
//            console.log('reCAPTCHA verification failed!');
//          }
//        });
//      }
//
//      // Thêm hộp kiểm reCAPTCHA vào trang web của bạn
//      grecaptcha.ready(function() {
//        grecaptcha.execute('6LequfgkAAAAANl1Q3A-bKNvwLoGJcrqpfcQH7R4', {action: 'submit'}).then(function(token) {
//          // Đưa token vào hàm onSubmit để xác minh
//          onSubmit(token);
//        });
//      });
// }