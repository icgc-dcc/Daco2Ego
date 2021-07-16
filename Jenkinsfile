def commit = "UNKNOWN" 
pipeline {
    agent {
        kubernetes {
            label 'daco2ego-executor'
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: helm
    image: alpine/helm:2.12.3
    command:
    - cat
    tty: true
  - name: docker
    image: docker:18-git
    tty: true
    env:
      - name: DOCKER_HOST
        value: tcp://localhost:2375
  - name: dind-daemon
    image: docker:18.06-dind
    securityContext:
      privileged: true
      runAsUser: 0
    volumeMounts:
      - name: docker-graph-storage
        mountPath: /var/lib/docker
  securityContext:
    runAsUser: 1000
  volumes:
  - name: docker-graph-storage
    emptyDir: {}
"""
        }
    }
    stages {
        stage('Build') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(credentialsId:'argoDockerHub', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                        sh 'docker login -u $USERNAME -p $PASSWORD'
                    }
                    script {
                        commit = sh(returnStdout: true, script: 'git describe --always').trim()
                    }

                    // DNS error if --network is default
                    sh "docker build --network=host . -t icgcargo/daco2ego:${commit}"

                    sh "docker push icgcargo/daco2ego:${commit}"
                }
            }
        }

        stage('Deploy to argo-dev') {
            when { branch 'develop' }
            steps {
               container('docker') {
                    withCredentials([usernamePassword(credentialsId:'argoDockerHub', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                        sh 'docker login -u $USERNAME -p $PASSWORD'
                    }

                    // the network=host needed to download dependencies using the host network (since we are inside 'docker'
                    // container)
                    sh "docker build --network=host -f Dockerfile . -t icgcargo/daco2ego:edge"
                    sh "docker push icgcargo/daco2ego:edge"
               }
                build(job: "/ARGO/provision/daco2ego", parameters: [
                     [$class: 'StringParameterValue', name: 'AP_ARGO_ENV', value: 'dev' ],
                     [$class: 'StringParameterValue', name: 'AP_ARGS_LINE', value: "--set-string image.tag=${commit}" ]
                ])
            }
        }

        stage('Deploy to argo-qa') {
            when { branch 'master' }
            steps {
               container('docker') {
                    withCredentials([usernamePassword(credentialsId:'argoDockerHub', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                        sh 'docker login -u $USERNAME -p $PASSWORD'
                    }

                    // the network=host needed to download dependencies using the host network (since we are inside 'docker'
                    // container)
                    sh "docker build --network=host -f Dockerfile . -t icgcargo/daco2ego:latest"
                    sh "docker push icgcargo/daco2ego:latest"
                    withCredentials([usernamePassword(credentialsId: 'argoGithub', passwordVariable: 'GIT_PASSWORD', usernameVariable: 'GIT_USERNAME')]) {
                        sh "git tag ${commit}"
                        sh "git push https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/icgc-argo/daco2ego --tags"
                    }
                }
                build(job: "/ARGO/provision/daco2ego", parameters: [
                     [$class: 'StringParameterValue', name: 'AP_ARGO_ENV', value: 'qa' ],
                     [$class: 'StringParameterValue', name: 'AP_ARGS_LINE', value: "--set-string image.tag=${commit}" ]
                ])
            }
        }

    }

    post {
        always 
    }
 
}
