# step 1
docker-compose build

# step 2 
docker-compose up

# step 3
POST http://localhost:5000/api/v1/captcha/
body{
    data: base64 captcha
}