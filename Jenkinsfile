pipeline {
  agent any
  stages {
    stage('Build') {
      parallel {
        stage('Slice Manager') {
          steps {
            echo 'Building Slice Manager container'
            sh 'docker build -t registry.sonata-nfv.eu:5000/tng-slice-mngr .'
          }
        }
      }
    }
    stage('Unittest Dependencies') {
      steps {
        sh 'echo TODO Unit Tests Dependencies'
      }
    }
    stage('Unittest execution'){
      parallel {
        stage('Performing Unit Tests') {
          steps {
            sh 'echo TODO Unit Tests'
          }
        } 
      }
    }
    stage('Checkstyle') {
      parallel {
        stage('Slice Manager') {
          steps {
            sh 'echo TODO Checkstyle pep8'
          }
        }
      }
    }
    stage('Publish to :latest') {
      parallel {
        stage('Slice Manager') {
          steps {
            echo 'Publishing Slice Manager container'
            sh 'docker push registry.sonata-nfv.eu:5000/tng-slice-mngr'
          }
        }
      }
    }
    stage('Deploying in pre-integration ') {
      when{
        not{
          branch 'master'
        }        
      }      
      steps {
        sh 'rm -rf tng-devops || true'
        sh 'git clone https://github.com/sonata-nfv/tng-devops.git'
        dir(path: 'tng-devops') {
          sh 'ansible-playbook roles/sp.yml -i environments -e "target=pre-int-sp"'
        }
      }
    }
    stage('Publishing to :int') {
      when{
        branch 'master'
      }      
      parallel {
        stage('Slice Manager') {
          steps {
            echo 'Publishing Slice Manager container'
            sh 'docker tag registry.sonata-nfv.eu:5000/tng-slice-mngr:latest registry.sonata-nfv.eu:5000/tng-slice-mngr:int'
            sh 'docker push registry.sonata-nfv.eu:5000/tng-slice-mngr:int'
          }
        }
      }
    }
    stage('Deploying in integration') {
      when{
        branch 'master'
      }      
      steps {
        sh 'docker tag registry.sonata-nfv.eu:5000/tng-slice-mngr:latest registry.sonata-nfv.eu:5000/tng-slice-mngr:int'
        sh 'docker push registry.sonata-nfv.eu:5000/tng-slice-mngr:int'
        sh 'rm -rf tng-devops || true'
        sh 'git clone https://github.com/sonata-nfv/tng-devops.git'
        dir(path: 'tng-devops') {
          sh 'ansible-playbook roles/sp.yml -i environments -e "target=int-sp"'
        }
      }
    }
  }
  post {
    always {
      echo 'Clean Up'
      sh 'echo TODO Clean environment'
    }
    success {
        emailext (
          subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
          body: """<p>SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
            <p>Check console output at &QUOT;<a href='${env.BUILD_URL}'>${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>&QUOT;</p>""",
        recipientProviders: [[$class: 'DevelopersRecipientProvider']]
        )
      }
    failure {
      emailext (
          subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
          body: """<p>FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
            <p>Check console output at &QUOT;<a href='${env.BUILD_URL}'>${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>&QUOT;</p>""",
          recipientProviders: [[$class: 'DevelopersRecipientProvider']]
        )
    }  
  }
}
