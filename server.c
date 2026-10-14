#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define MAX_CLIENTS 10


typedef struct{
    int fd;
    char name[32];
    int has_name;
    int handshake_status;
    SSL *ssl;
}Client;

void remove_newline(char* array){
    char* nl = strchr(array,'\n');
    if(nl) *nl = '\0';
}

int main(){
    OPENSSL_init_ssl(0,NULL);

    SSL_CTX* ctx = SSL_CTX_new(TLS_server_method());
    if(ctx == NULL){
        ERR_print_errors_fp(stderr);
        return 1;
    }

    int certificate = SSL_CTX_use_certificate_file(ctx,"server.crt",SSL_FILETYPE_PEM);
    if(certificate <= 0){
        ERR_print_errors_fp(stderr);
        return 1;
    }

    int privat_key = SSL_CTX_use_PrivateKey_file(ctx,"server.key",SSL_FILETYPE_PEM);
    if(privat_key <= 0){
        ERR_print_errors_fp(stderr);
        return 1;
    }

    int server_fd = socket(AF_INET,SOCK_STREAM,0);
    if(server_fd == -1){
        perror("socket");
        return 1;
    }
    int opt = 1;
    setsockopt(server_fd,SOL_SOCKET,SO_REUSEADDR,&opt,sizeof(opt));
    
    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(5050);

    int b = bind(server_fd,(struct sockaddr*)&addr,sizeof(addr));
    if(b == -1){
        perror("bind");
        return 1;
    }
    
    int l = listen(server_fd,MAX_CLIENTS);
    if(l == -1){
        perror("listen");
        return 1;
    }
    printf("Server listening in port 5050...\n");

    int count = 0;
    Client clients[MAX_CLIENTS];

     while(1){
        fd_set readfds;
        FD_ZERO(&readfds);

        FD_SET(server_fd,&readfds);
        for(int i = 0;i < count;i++){
            FD_SET(clients[i].fd,&readfds);
        }

        int max_fd = server_fd;
        for(int i = 0; i < count;i++){
            if(max_fd < clients[i].fd) max_fd = clients[i].fd;
        }

        int s = select(max_fd + 1,&readfds,NULL,NULL,NULL);
        if(s == -1){
            perror("select");
            return 1;
        }

        if(FD_ISSET(server_fd,&readfds)){
            if(count < MAX_CLIENTS){
                clients[count].fd = accept(server_fd,NULL,NULL);

                if(clients[count].fd == -1){
                    perror("accept");
                }
                else{
                    clients[count].ssl = SSL_new(ctx);
                    int set_fd_res = SSL_set_fd(clients[count].ssl,clients[count].fd);
                    if(set_fd_res != 1){
                        perror("SSL_set_fd");
                    }
                    clients[count].has_name = 0;
                    clients[count].handshake_status = 0;
                    count++;
                }
            }
            else{
                int many_fd = accept(server_fd,NULL,NULL);
                if(many_fd == -1){
                    perror("accept");
                }
                close(many_fd);
            }
        }
        char buf[1024];
        for(int i = 0; i < count;i++){
            if(!FD_ISSET(clients[i].fd,&readfds)){
                continue;
            }
            if(clients[i].handshake_status == 0){
                int accept_result = SSL_accept(clients[i].ssl);
                if(accept_result == 1){
                    clients[i].handshake_status = 1;
                    printf("Handhake done for fd = %d\n",clients[i].fd);
                    SSL_write(clients[i].ssl,"Enter you name: ",17);
                }
                else{
                    int err = SSL_get_error(clients[i].ssl,accept_result);
                    if(err == SSL_ERROR_WANT_READ||err == SSL_ERROR_WANT_WRITE){
                        continue;
                    }
                    SSL_free(clients[i].ssl);
                    close(clients[i].fd);
                    clients[i] = clients[count-1];
                    count--;
                    i--;
                }
                continue;
            }
            else if(clients[i].handshake_status == 1){
                int n = SSL_read(clients[i].ssl,buf,sizeof(buf)-1);
                if(n == 0){
                    SSL_free(clients[i].ssl);
                    close(clients[i].fd);
                    clients[i] = clients[count-1];
                    count--;
                    i--;
                }
                else if(n < 0){
                    printf("Error in client %d",count);
                    SSL_free(clients[i].ssl);
                    close(clients[i].fd);
                    clients[i] = clients[count-1];
                    count--;
                    i--;
                }
                else if(n > 0){
                    remove_newline(buf);
                    if(clients[i].has_name == 0){
                        strncpy(clients[i].name,buf,31);
                        clients[i].name[31] = '\0';
                        remove_newline(clients[i].name);

                        clients[i].has_name = 1;
                        SSL_write(clients[i].ssl,"Welcome to my C server!\n",24);
                    }
                        else if(clients[i].has_name == 1){
                            char output[1100];
                            int len = snprintf(output,sizeof(output),"[%s]: %s\n",clients[i].name,buf);
                            for(int j = 0;j < count; j++){
                                if(clients[j].fd!=clients[i].fd && clients[j].has_name == 1){
                                    SSL_write(clients[j].ssl,output,len);
                                }
                            }
                    }
                }     
            }
        }
    }
}
