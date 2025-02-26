# wordpress/Dockerfile
FROM wordpress:latest

# PHP 설정 최적화
RUN { \
    echo 'upload_max_filesize = 64M'; \
    echo 'post_max_size = 64M'; \
    echo 'memory_limit = 256M'; \
    echo 'max_execution_time = 300'; \
    echo 'max_input_vars = 3000'; \
    } > /usr/local/etc/php/conf.d/wordpress.ini

# 추가 PHP 확장 설치 (필요시)
RUN docker-php-ext-install exif

# WP-CLI 설치 (WordPress 명령줄 도구)
RUN curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
    && chmod +x wp-cli.phar \
    && mv wp-cli.phar /usr/local/bin/wp
