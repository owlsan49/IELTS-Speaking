<script setup lang="ts">
import { GetInfo, PushAudios } from "@/apis/read.js"
import { ref, onMounted, onUnmounted } from 'vue'
import { Mic } from '@element-plus/icons-vue'

let ques_info = ref()
const recording = ref(false)
const mediaRecorder = ref()
const chunks = ref([])
const audioURL = ref({})
const blob = ref()
const audioText = ref()
const loading = ref(false)
let currentIdx = -1
let stream
const audioSet = new FormData()

onMounted(async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        console.log('授权成功！')
        mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm; codecs=opus' })
        mediaRecorder.value.ondataavailable = (e) => {
            chunks.value.push(e.data)
        }

        mediaRecorder.value.onstop = () => {
            blob.value = new Blob(chunks.value, { type: 'audio/webm; codecs=opus' })
            chunks.value = []
            audioURL.value[currentIdx.toString()] = URL.createObjectURL(blob.value)
            audioSet.set(currentIdx.toString(), blob.value, `audio_${currentIdx}.webm`)

        }
    } catch (error) {
        console.error('获取音频输入设备失败：', error)
    }
})

function toggleRecording(idx) {
    if (recording.value) {
        mediaRecorder.value.stop()
        recording.value = false
    } else {
        mediaRecorder.value.start()
        recording.value = true
        currentIdx = idx
    }
}

function closeStream(stream) {
    if (stream) {
        console.log(stream.getTracks())
        stream.getTracks().forEach((track) => track.stop())
    }
}

onUnmounted(() => {
    closeStream(stream)
})

function recite() {
    loading.value = true
    GetInfo({})
        .then((response: any) => {
            loading.value = false
            ques_info.value = response.data.ques_info
            // console.log("@", ques_info)
        })
        .catch((error: any) => {
            loading.value = false
            console.log("@, error")
        })
}

function submit() {
    loading.value = true
    PushAudios(audioSet)
        .then((response: any) => {
            audioText.value = response.data.audio_text
            loading.value = false
            console.log("@", audioText.value)
        })
        .catch((error: any) => {
            loading.value = false
            console.log("@22, error")
        })
}
</script>

<template>
    <el-button type="primary" @click="recite" v-loading="loading">Recite</el-button>
    <h3 v-if="ques_info">Today we have {{ ques_info.length }} questions!!</h3>
    <hr />
    <div v-for="ques in ques_info" :key="ques[0]" class="container_cont">
        <div class="each_cont">
            <h4>{{ ques[2] }}</h4>
            <h5>{{ ques[3] }}</h5>
            <el-button type="danger" :icon="Mic" circle @click="toggleRecording(ques[0])" v-if="!recording" />
            <el-button type="" :icon="Mic" circle @click="toggleRecording(ques[0])" v-else />
            <audio class="audio-player" controls :src="audioURL[ques[0].toString()]" preload="auto"></audio>
        </div>
        <div class="each_cont" v-if="audioText && ques[0] in audioText">
            {{ audioText[ques[0]] }}
        </div>
        <hr style="border-top: 1px dashed #000; border-bottom: none;" />
    </div>

    <el-button type="primary" @click="submit" v-loading="loading">Submit</el-button>

</template>

<style>
</style>
