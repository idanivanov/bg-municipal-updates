# bg-municipal-updates

1. Install Anaconda:

    ```sh
    > wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    > chmod +x ./Miniconda3-latest-Linux-x86_64.sh
    > ./Miniconda3-latest-Linux-x86_64.sh
    ```

    And then follow the instructions.

2. Deploy to a remote VM:

    ```sh
    > cd {path_to_the_repo_directory}/..
    > scp [-P PORT] -r ./bg-municipal-updates {username}@{remote_host}:./ [-p 23]
    ```

3. Install Chrome:

    ```sh
    > wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    > sudo dpkg -i google-chrome-stable_current_amd64.deb
    ```

4. Prepare the python environment:

    ```sh
    > cd {path_to_the_repo_directory}
    > pip install -r requirements.txt
    > pip install "dash[diskcache]"
    ```

5. Expose port 8050

    ```sh
    > ufw allow 8050/tcp
    ```

6. Configure recaptcha - fill in your reCAPTCHA SITEKEY and SECRET in file `main.py`.

7. Run the server:

    ```sh
    > cd {path_to_the_repo_directory}
    > python main.py
    ```
