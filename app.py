from flask import Flask, jsonify, request

app = Flask(__name__)

# 模拟部署状态数据
deployments = {}


@app.route('/')
def index():
    """首页路由"""
    return jsonify({
        'message': '欢迎使用自动化部署流水线系统',
        'endpoints': [
            '/',
            '/api/deployments',
            '/api/deploy/<pipeline_id>',
            '/api/deploy',
            '/api/status/<pipeline_id>'
        ]
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
        'steps': []
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

    return jsonify(deployments[pipeline_id])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
