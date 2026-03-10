from flask import Flask, jsonify, request, g
from datetime import datetime
import subprocess
import json
import requests
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Request ID middleware
@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{g.request_id}] {request.method} {request.path}")

@app.after_request
def after_request(response):
    logger.info(f"[{g.request_id}] Status: {response.status_code}")
    response.headers['X-Request-ID'] = g.request_id
    return response

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'request_id': g.request_id}), 200

# Error handlers
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Not Found', 'message': 'Resource not found', 'request_id': g.request_id}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 Internal Error: {e}")
    return jsonify({'error': 'Internal Server Error', 'message': 'Something went wrong', 'request_id': g.request_id}), 500

# 模拟部署状态数据
deployments = {}

# 测试报告存储
test_reports = {}

# Webhook配置存储
webhooks = {}


@app.route('/')
def index():
    """首页路由"""
    return jsonify({
        'message': '欢迎使用自动化部署流水线系统',
        'endpoints': {
            'deployments': [
                'GET /api/deployments',
                'GET /api/deploy/<pipeline_id>',
                'POST /api/deploy',
                'PUT /api/status/<pipeline_id>',
                'DELETE /api/deploy/<pipeline_id>'
            ],
            'docker': [
                'POST /api/docker/build',
                'POST /api/docker/run',
                'GET /api/docker/images'
            ],
            'test_reports': [
                'GET /api/test-reports',
                'GET /api/test-reports/<report_id>',
                'POST /api/test-reports',
                'DELETE /api/test-reports/<report_id>'
            ],
            'webhooks': [
                'GET /api/webhooks',
                'POST /api/webhooks',
                'DELETE /api/webhooks/<webhook_id>',
                'POST /api/webhooks/test'
            ]
        }
    })


@app.route('/api/deployments', methods=['GET'])
def get_deployments():
    """获取所有部署记录"""
    return jsonify({
        'deployments': list(deployments.values())
    })


@app.route('/api/deploy/<pipeline_id>', methods=['GET'])
def get_deployment(pipeline_id):
    """获取特定部署流水线的状态"""
    if pipeline_id in deployments:
        return jsonify(deployments[pipeline_id])
    return jsonify({'error': '部署流水线不存在'}), 404


@app.route('/api/deploy', methods=['POST'])
def create_deployment():
    """创建新的部署任务"""
    data = request.get_json() or {}
    pipeline_id = data.get('pipeline_id', f"pipeline-{len(deployments) + 1}")

    deployment = {
        'pipeline_id': pipeline_id,
        'status': 'pending',
        'message': '部署任务已创建',
        'steps': [],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    deployments[pipeline_id] = deployment

    return jsonify({
        'message': '部署任务创建成功',
        'deployment': deployment
    }), 201


@app.route('/api/status/<pipeline_id>', methods=['PUT'])
def update_status(pipeline_id):
    """更新部署状态"""
    if pipeline_id not in deployments:
        return jsonify({'error': '部署流水线不存在'}), 404

    data = request.get_json() or {}
    deployments[pipeline_id]['status'] = data.get('status', 'pending')
    deployments[pipeline_id]['message'] = data.get('message', '')
    deployments[pipeline_id]['updated_at'] = datetime.now().isoformat()

    return jsonify(deployments[pipeline_id])


@app.route('/api/deploy/<pipeline_id>', methods=['DELETE'])
def delete_deployment(pipeline_id):
    """删除部署任务"""
    if pipeline_id not in deployments:
        return jsonify({'error': '部署流水线不存在'}), 404

    del deployments[pipeline_id]
    return jsonify({'message': '部署任务已删除'})


# ============ Docker 支持 ============

@app.route('/api/docker/build', methods=['POST'])
def docker_build():
    """构建Docker镜像"""
    data = request.get_json() or {}
    dockerfile = data.get('dockerfile', 'Dockerfile')
    image_name = data.get('image_name', 'ci-build-image')
    tag = data.get('tag', 'latest')
    context = data.get('context', '.')

    full_image = f"{image_name}:{tag}"

    try:
        result = subprocess.run(
            ['docker', 'build', '-t', full_image, '-f', dockerfile, context],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0:
            return jsonify({
                'message': 'Docker镜像构建成功',
                'image': full_image,
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': 'Docker镜像构建失败',
                'output': result.stderr
            }), 500
    except FileNotFoundError:
        return jsonify({'error': 'Docker未安装或不在PATH中'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docker/run', methods=['POST'])
def docker_run():
    """运行Docker容器"""
    data = request.get_json() or {}
    image = data.get('image')
    container_name = data.get('container_name', f"container-{uuid.uuid4().hex[:8]}")
    command = data.get('command')
    detach = data.get('detach', False)

    if not image:
        return jsonify({'error': '需要提供镜像名称'}), 400

    cmd = ['docker', 'run']

    if detach:
        cmd.append('-d')
    else:
        cmd.append('--rm')

    if container_name:
        cmd.extend(['--name', container_name])

    if command:
        cmd.extend(['sh', '-c', command])

    cmd.append(image)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return jsonify({
                'message': '容器运行成功',
                'container_name': container_name,
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': '容器运行失败',
                'output': result.stderr
            }), 500
    except FileNotFoundError:
        return jsonify({'error': 'Docker未安装或不在PATH中'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docker/images', methods=['GET'])
def docker_images():
    """列出Docker镜像"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        images = [img.strip() for img in result.stdout.strip().split('\n') if img.strip()]
        return jsonify({'images': images})
    except FileNotFoundError:
        return jsonify({'error': 'Docker未安装或不在PATH中'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 测试报告 ============

@app.route('/api/test-reports', methods=['GET'])
def get_test_reports():
    """获取所有测试报告"""
    return jsonify({'test_reports': list(test_reports.values())})


@app.route('/api/test-reports/<report_id>', methods=['GET'])
def get_test_report(report_id):
    """获取特定测试报告"""
    if report_id in test_reports:
        return jsonify(test_reports[report_id])
    return jsonify({'error': '测试报告不存在'}), 404


@app.route('/api/test-reports', methods=['POST'])
def create_test_report():
    """创建测试报告"""
    data = request.get_json() or {}
    report_id = data.get('report_id', f"report-{uuid.uuid4().hex[:8]}")

    report = {
        'report_id': report_id,
        'pipeline_id': data.get('pipeline_id'),
        'test_type': data.get('test_type', 'unit'),
        'status': data.get('status', 'passed'),
        'total_tests': data.get('total_tests', 0),
        'passed': data.get('passed', 0),
        'failed': data.get('failed', 0),
        'skipped': data.get('skipped', 0),
        'duration': data.get('duration', 0),
        'logs': data.get('logs', ''),
        'created_at': datetime.now().isoformat()
    }

    test_reports[report_id] = report
    return jsonify({
        'message': '测试报告创建成功',
        'report': report
    }), 201


@app.route('/api/test-reports/<report_id>', methods=['DELETE'])
def delete_test_report(report_id):
    """删除测试报告"""
    if report_id not in test_reports:
        return jsonify({'error': '测试报告不存在'}), 404

    del test_reports[report_id]
    return jsonify({'message': '测试报告已删除'})


# ============ Webhook 集成 ============

@app.route('/api/webhooks', methods=['GET'])
def get_webhooks():
    """获取所有Webhook配置"""
    return jsonify({'webhooks': list(webhooks.values())})


@app.route('/api/webhooks', methods=['POST'])
def create_webhook():
    """创建Webhook配置"""
    data = request.get_json() or {}
    webhook_id = data.get('webhook_id', f"webhook-{uuid.uuid4().hex[:8]}")

    webhook = {
        'webhook_id': webhook_id,
        'url': data.get('url'),
        'events': data.get('events', ['deployment.created', 'deployment.completed']),
        'active': data.get('active', True),
        'secret': data.get('secret', ''),
        'created_at': datetime.now().isoformat()
    }

    if not webhook['url']:
        return jsonify({'error': '需要提供Webhook URL'}), 400

    webhooks[webhook_id] = webhook
    return jsonify({
        'message': 'Webhook创建成功',
        'webhook': webhook
    }), 201


@app.route('/api/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """删除Webhook配置"""
    if webhook_id not in webhooks:
        return jsonify({'error': 'Webhook不存在'}), 404

    del webhooks[webhook_id]
    return jsonify({'message': 'Webhook已删除'})


def trigger_webhooks(event, data):
    """触发Webhooks"""
    for webhook_id, webhook in webhooks.items():
        if webhook['active'] and event in webhook['events']:
            try:
                payload = {
                    'event': event,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
                requests.post(webhook['url'], json=payload, timeout=10)
            except Exception as e:
                print(f"Webhook触发失败: {webhook_id}, 错误: {e}")


@app.route('/api/webhooks/test', methods=['POST'])
def test_webhook():
    """测试Webhook"""
    data = request.get_json() or {}
    url = data.get('url')

    if not url:
        return jsonify({'error': '需要提供测试URL'}), 400

    try:
        payload = {
            'event': 'test',
            'timestamp': datetime.now().isoformat(),
            'data': {'message': '这是测试 webhook'}
        }
        response = requests.post(url, json=payload, timeout=10)
        return jsonify({
            'message': 'Webhook测试成功',
            'status_code': response.status_code
        })
    except Exception as e:
        return jsonify({'error': f'Webhook测试失败: {str(e)}'}), 500


@app.route('/api/deployments', methods=['POST'])
def trigger_deployment_webhooks():
    """部署创建时触发webhooks"""
    data = request.get_json() or {}
    pipeline_id = data.get('pipeline_id', f"pipeline-{len(deployments) + 1}")
    trigger_webhooks('deployment.created', {'pipeline_id': pipeline_id})
    return jsonify({'message': '部署webhook已触发'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
