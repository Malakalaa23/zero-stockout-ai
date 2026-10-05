[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1480[m[36m:[m            "Requirement already satisfied: [1;31mtoken[mizers<1,>=0.15 in /usr/local/lib/python3.13/dist-packages (from cohere) (0.23.1)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1493[m[36m:[m            "Requirement already satisfied: huggingface-hub<2.0,>=0.16.4 in /usr/local/lib/python3.13/dist-packages (from [1;31mtoken[mizers<1,>=0.15->cohere) (1.29.0)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1494[m[36m:[m            "Requirement already satisfied: click<9.0.0,>=8.4.2 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (8.5.0)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1495[m[36m:[m            "Requirement already satisfied: filelock>=3.10.0 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (3.32.5)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1496[m[36m:[m            "Requirement already satisfied: fsspec>=2023.5.0 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (2025.12.0)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1497[m[36m:[m            "Requirement already satisfied: hf-xet<2.0.0,>=1.5.2 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (1.6.0)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1498[m[36m:[m            "Requirement already satisfied: packaging>=20.9 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (26.3)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1499[m[36m:[m            "Requirement already satisfied: pyyaml>=5.1 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (6.0.3)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1500[m[36m:[m            "Requirement already satisfied: tqdm>=4.42.1 in /usr/local/lib/python3.13/dist-packages (from huggingface-hub<2.0,>=0.16.4->[1;31mtoken[mizers<1,>=0.15->cohere) (4.67.3)\n",
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1518[m[36m:[m        "os.environ[\"COHERE_[1;31mAPI_KEY[m\"] = getpass(\"Enter your Cohere API key: \")"
[35mZero_stockout_router_agent (5).ipynb[m[36m:[m[32m1543[m[36m:[m        "co = cohere.ClientV2(os.environ[\"COHERE_[1;31mAPI_KEY[m\"])"
[35maudit_system.py[m[36m:[m[32m496[m[36m:[m            if "[1;31mpassword[m" in content.lower() and "os.getenv" not in content:
[35maudit_system.py[m[36m:[m[32m497[m[36m:[m                self.log_warn("Possible hardcoded [1;31msecret[m in config.py")
[35maudit_system.py[m[36m:[m[32m498[m[36m:[m            elif "[1;31mpassword[m" in content.lower():
[35maudit_system.py[m[36m:[m[32m499[m[36m:[m                self.log_pass("[1;31mSecret[ms appear to use environment variables")
[35maudit_system.py[m[36m:[m[32m501[m[36m:[m                self.log_info("No [1;31msecret[ms found in config.py")
[35mbackend/config.py[m[36m:[m[32m18[m[36m:[m    POSTGRES_[1;31mPASSWORD[m: str = os.getenv("POSTGRES_[1;31mPASSWORD[m", "oraclepass")
[35mbackend/config.py[m[36m:[m[32m26[m[36m:[m        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_[1;31mPASSWORD[m}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
[35mbackend/config.py[m[36m:[m[32m40[m[36m:[m    NEO4J_[1;31mPASSWORD[m: str = os.getenv("NEO4J_[1;31mPASSWORD[m", "neo4jpass")
[35mbackend/config.py[m[36m:[m[32m52[m[36m:[m    [1;31mSECRET[m_KEY: str = os.getenv("[1;31mSECRET[m_KEY", "dev-[1;31msecret[m-key-change-in-production")
[35mbackend/config.py[m[36m:[m[32m75[m[36m:[m    if config.POSTGRES_[1;31mPASSWORD[m == "oraclepass" and config.DEBUG is False:
[35mbackend/config.py[m[36m:[m[32m76[m[36m:[m        print("⚠️  WARNING: Using default PostgreSQL [1;31mpassword[m in production!")
[35mbackend/config.py[m[36m:[m[32m78[m[36m:[m    if config.[1;31mSECRET[m_KEY == "dev-[1;31msecret[m-key-change-in-production" and config.DEBUG is False:
[35mbackend/config.py[m[36m:[m[32m79[m[36m:[m        print("⚠️  WARNING: Using default [1;31mSECRET[m_KEY in production!")
[35mdocker-compose.yml[m[36m:[m[32m7[m[36m:[m      POSTGRES_[1;31mPASSWORD[m: admin
[35mdocker-compose.yml[m[36m:[m[32m34[m[36m:[m      NEO4J_AUTH: neo4j/[1;31mpassword[m
[35mdocker-compose.yml[m[36m:[m[32m41[m[36m:[m      test: ['CMD', 'cypher-shell', '-u', 'neo4j', '-p', '[1;31mpassword[m', 'RETURN 1']
[35mdocker-compose.yml[m[36m:[m[32m80[m[36m:[m      NEO4J_[1;31mPASSWORD[m: [1;31mpassword[m
