pipeline {
    agent any

    stages {
        stage('Hello') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Checkout SCM'){
            steps {
		checkout scm
    	    	}
	    	}
        }
        stage('SonarQube Analysis'){
            environment{
                SCANNER_HOME= tool 'Sonar-Scanner'
            }
            steps{
                withSonarQubeEnv('SonarQube-Server') {
                    sh '''
                        pwd
			$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectVersion=$BUILD_NUMBER
                        echo $SONAR_HOST_URL
                        rm -rf DCLV/sonar-report
                        java -jar /opt/sonarqube/extensions/plugins/sonar-cnes-report-4.1.3.jar -t $SONAR_AUTH_TOKEN -s $SONAR_HOST_URL -p nam.nguyen.tuan_dclv_AYRbjM3DrqufXX4VQSfP -o DCLV/sonar-report
                    '''
                    println "${env.SONAR_HOST_URL}"
                }
            	withCredentials([usernamePassword(credentialsId: 'eb2a6a8c-7223-4f46-82ec-130fb148f747', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        git config --global user.email "you@example.com"
                        git config --global user.name "Your Name"
                        cd  $WORKSPACE/DCLV
                        git add sonar-report/*
                        git commit -m "SonarQube report for $BUILD_NUMBER"
                        git push https://$USER:$PASS@github.com/namnt2307/DCLV.git
                    '''
            	}
            }
       }
        stage("Quality Gate") {
            steps {
              timeout(time: 1, unit: 'HOURS') {
                waitForQualityGate abortPipeline: true
              }
            }
        }       
    }
}

