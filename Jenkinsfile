pipeline {
  agent any

  environment {
    DOCKER_IMAGE = "yourdockerhubuser/warehouse_app:${env.BUILD_NUMBER}"
    STAGE_HOST = "85.239.144.132"
    STAGE_PORT = "47324"
    STAGE_USER = "kernys"
    STAGE_STAGE_PATH = "/home/kernys/warehouse_app_stage"
    STAGE_PROD_PATH = "/home/kernys/warehouse_app"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Static Analysis') {
      steps {
        sh 'bandit -r . -f csv -o out.csv'
        sh 'flake8 ./src'
        sh 'mypy ./src'
      }
    }

    stage('Unit Tests') {
      steps {
        sh 'pytest tests/'
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build -t $DOCKER_IMAGE .'
      }
    }

    stage('Push to Docker Hub') {
      when {
        anyOf {
          branch 'dev'
          branch 'main'
        }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
          sh 'docker push $DOCKER_IMAGE'
        }
      }
    }

    stage('Deploy to STAGE') {
      when {
        branch 'dev'
      }
      steps {
        sh 'ssh -p $STAGE_PORT $STAGE_USER@$STAGE_HOST "cd $STAGE_STAGE_PATH && docker-compose pull && docker-compose up -d"'
      }
    }

    stage('Deploy to PROD') {
      when {
        branch 'main'
      }
      steps {
        sh 'ssh -p $STAGE_PORT $STAGE_USER@$STAGE_HOST "cd $STAGE_PROD_PATH && docker-compose pull && docker-compose up -d"'
      }
    }

    stage('SQL Security Check') {
      steps {
        sh 'sql-analyzer ./data/*.sql'
      }
    }

    stage('Compare DB Schemas') {
      when {
        branch 'dev'
      }
      steps {
        sh 'db-schema-diff data/test_schema.sql data/stage_schema.sql'
      }
    }

    stage('Apply DB Migration to STAGE') {
      when {
        branch 'dev'
      }
      steps {
        sh 'ssh -p $STAGE_PORT $STAGE_USER@$STAGE_HOST "psql -U user -d dbname -f $STAGE_STAGE_PATH/data/migration.sql"'
      }
    }

    stage('Backup PROD DB') {
      when {
        branch 'main'
      }
      steps {
        sh 'ssh -p $STAGE_PORT $STAGE_USER@$STAGE_HOST "pg_dump -U user dbname > $STAGE_PROD_PATH/backup_$(date +%F).sql"'
      }
    }

    stage('Apply DB Migration to PROD') {
      when {
        branch 'main'
      }
      steps {
        sh 'ssh -p $STAGE_PORT $STAGE_USER@$STAGE_HOST "psql -U user -d dbname -f $STAGE_PROD_PATH/data/migration.sql"'
      }
    }
  }
}

