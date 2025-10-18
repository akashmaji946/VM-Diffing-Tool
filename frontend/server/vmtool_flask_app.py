#!/usr/bin/env python3
# file: vmtool_flask_app.py
# location: VM-Diffing-Tool/frontend/server/vmtool_flask_app.py
# author: Akash Maji
# date: 2025-10-18
# version: 0.1
# description: Flask web application for VM disk comparison and block data viewing

from flask import Flask, render_template, request, jsonify
import vmtool
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare')
def compare_page():
    return render_template('compare.html')

@app.route('/block-data')
def block_data_page():
    return render_template('block_data.html')

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """API endpoint to compare two disk images"""
    try:
        data = request.json
        disk1 = data.get('disk1')
        disk2 = data.get('disk2')
        block_size = int(data.get('block_size', 4096))
        start_block = int(data.get('start_block', 0))
        end_block = int(data.get('end_block', -1))
        
        if not disk1 or not disk2:
            return jsonify({'error': 'Both disk paths are required'}), 400
        
        if not os.path.exists(disk1):
            return jsonify({'error': f'Disk 1 not found: {disk1}'}), 400
        
        if not os.path.exists(disk2):
            return jsonify({'error': f'Disk 2 not found: {disk2}'}), 400
        
        # Call vmtool to compare disks
        result = vmtool.list_blocks_difference_in_disks(
            disk1, disk2, block_size, start_block, end_block
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/block-data', methods=['POST'])
def api_block_data():
    """API endpoint to get block data from a disk"""
    try:
        data = request.json
        disk = data.get('disk')
        block_number = int(data.get('block_number'))
        block_size = int(data.get('block_size', 4096))
        format_type = data.get('format', 'hex')
        
        if not disk:
            return jsonify({'error': 'Disk path is required'}), 400
        
        if not os.path.exists(disk):
            return jsonify({'error': f'Disk not found: {disk}'}), 400
        
        # Call vmtool to get block data
        result = vmtool.get_block_data_in_disk(
            disk, block_number, block_size, format_type
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
