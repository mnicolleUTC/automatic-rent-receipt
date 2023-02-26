# Build docker 
# docker build --no-cache -t mnicolle/latex_with_python .
# Run docker for debug (-it)
# docker run -it -v "$(pwd):/data" mnicolle/latex_with_python

FROM blang/latex:ctanbasic

# Define working directory
WORKDIR /data
VOLUME ["/data"]

# Install Python
RUN apt-get update
RUN apt-get install -y build-essential wget libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev
RUN wget https://www.python.org/ftp/python/3.9.2/Python-3.9.2.tgz
RUN tar xvf Python-3.9.2.tgz
RUN cd Python-3.9.2 && ./configure && make && make install

#Install complementary package for Latex
RUN apt-get install locales -y
RUN locale-gen fr_FR.UTF-8
RUN echo "LANG=fr_FR.UTF-8" > /etc/default/locale
RUN mkdir /usr/local/texlive/2017/texmf-dist/tex/generic/babel-french
RUN tlmgr option repository ftp://tug.org/historic/systems/texlive/2017/tlnet-final
RUN tlmgr update --self
RUN tlmgr install ec
RUN tlmgr install cm-super
COPY french /data/french
RUN cp french/french.ldf french/francais.ldf french/acadian.ldf french/canadien.ldf french/frenchb.lua french/frenchb.ldf /usr/local/texlive/2017/texmf-dist/tex/generic/babel-french
RUN mktexlsr

# Install requirements package for python 
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Run python script and delete temp directory
CMD bash select_files.sh && python3 quittance.py && rm -rf /data/used_files





