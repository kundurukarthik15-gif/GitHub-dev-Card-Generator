FROM nginx:alpine

# Copy index.html to a template directory
COPY index.html /etc/nginx/templates/index.html.template

# Use an entrypoint script to substitute BACKEND_URL and start Nginx
# Nginx Alpine has a built-in feature to run envsubst on templates in /etc/nginx/templates/
# But it usually outputs to /etc/nginx/conf.d/. 
# Here we'll use a custom CMD to be explicit.

ENV BACKEND_URL=http://localhost:8080

CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/templates/index.html.template > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]

EXPOSE 80
