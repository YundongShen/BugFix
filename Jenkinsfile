pipeline {
  agent {
    node {
      label 'maven'
    }
  }
  stages {
    stage('dev Clone repository') {
      agent none
      when {
        branch 'eazytec_0.8.2_develop'
      }
      steps {
        git(url: 'https://gitlab.eazytec-cloud.com/fastdevelop/multiagent/metagpt', 
        credentialsId: 'gitlab-xiezhi', 
        branch: 'eazytec_0.8.2_develop',
        changelog: true, 
        poll: false
        )
      }
    }


    stage('prod Clone repository') {
      agent none
      when {
        branch 'eazytec_0.8.2_master'
      }
      steps {
        git(url: 'https://gitlab.eazytec-cloud.com/fastdevelop/multiagent/metagpt', credentialsId: 'gitlab-xiezhi', branch: 'eazytec_0.8.2_master', changelog: true, poll: false)
      }
    }

    stage('build') {
      agent none
      when {
        anyOf { branch 'eazytec_0.8.2_master'; branch 'eazytec_0.8.2_develop' }
      }
      steps {
       container('maven') {
          withCredentials([usernamePassword(credentialsId : 'harbor-user' ,passwordVariable : 'DOCKER_PASSWORD' ,usernameVariable : 'DOCKER_USERNAME' ,)]) {
            sh 'docker login -u "$DOCKER_USERNAME" -p "$DOCKER_PASSWORD"  $DOCKER_REPO'
            sh './build_and_push.sh'
          }
        }
      }
    }



     stage('deploy to test') {
            agent none
            when {
                    branch 'eazytec_0.8.2_develop'
                  }
            steps {
                 container ('maven') {
                      withCredentials([kubeconfigFile(credentialsId: 'kubeconfig',variable: 'KUBECONFIG')]) {
                          sh 'kubectl rollout restart deployment $DEPLOYMENT_NAME -n $NAMESPACE'
                    }
                }
            }
        }

    stage('deploy to master') {
            agent none
            when {
                    branch 'eazytec_0.8.2_master'
                  }
            steps {
                 container ('maven') {
                      withCredentials([kubeconfigFile(credentialsId: 'kubeconfig',variable: 'KUBECONFIG')]) {
                          sh 'kubectl rollout restart deployment $DEPLOYMENT_NAME_PROD -n $NAMESPACE'
                      }
                 }
             }
        }
  }
  environment {
    DOCKER_REPO = '47.103.57.78:30002'
    NAMESPACE = 'eazydevelop'
    DEPLOYMENT_NAME = 'metagpt-v1'
    DEPLOYMENT_NAME_PROD = 'metagpt-prod-v1'
  }
}